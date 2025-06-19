# tracking_app/utils.py - Updated with geolocation
import uuid
import socket
import subprocess
import platform
import json
import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('tracking_app')

def get_server_mac_address():
    """Get MAC address of the server machine"""
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                       for ele in range(0,8*6,8)][::-1])
        return mac
    except:
        return "unknown"

def get_ip_geolocation(ip_address):
    """
    Get geolocation data for an IP address using free APIs
    Uses caching to avoid repeated API calls for the same IP
    """
    # Skip geolocation for local/private IPs
    if ip_address.startswith(('127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
        return {
            'ip': ip_address,
            'city': 'Local Network',
            'country': 'Local',
            'country_code': 'LOC',
            'region': 'Local',
            'latitude': 0,
            'longitude': 0,
            'timezone': 'Local',
            'isp': 'Local Network',
            'is_local': True
        }
    
    # Check cache first
    cache_key = f"geo_{ip_address}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    geolocation_data = {
        'ip': ip_address,
        'city': 'Unknown',
        'country': 'Unknown',
        'country_code': 'UNK',
        'region': 'Unknown',
        'latitude': 0,
        'longitude': 0,
        'timezone': 'Unknown',
        'isp': 'Unknown',
        'is_local': False
    }
    
    # Try multiple free geolocation APIs
    apis = [
        {
            'url': f'http://ip-api.com/json/{ip_address}',
            'parser': lambda data: {
                'ip': ip_address,
                'city': data.get('city', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'country_code': data.get('countryCode', 'UNK'),
                'region': data.get('regionName', 'Unknown'),
                'latitude': data.get('lat', 0),
                'longitude': data.get('lon', 0),
                'timezone': data.get('timezone', 'Unknown'),
                'isp': data.get('isp', 'Unknown'),
                'is_local': False
            }
        },
        {
            'url': f'https://ipapi.co/{ip_address}/json/',
            'parser': lambda data: {
                'ip': ip_address,
                'city': data.get('city', 'Unknown'),
                'country': data.get('country_name', 'Unknown'),
                'country_code': data.get('country_code', 'UNK'),
                'region': data.get('region', 'Unknown'),
                'latitude': data.get('latitude', 0),
                'longitude': data.get('longitude', 0),
                'timezone': data.get('timezone', 'Unknown'),
                'isp': data.get('org', 'Unknown'),
                'is_local': False
            }
        }
    ]
    
    for api in apis:
        try:
            response = requests.get(api['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and not data.get('error'):
                    geolocation_data = api['parser'](data)
                    # Cache for 24 hours
                    cache.set(cache_key, geolocation_data, 86400)
                    logger.info(f"Got geolocation for {ip_address}: {geolocation_data['city']}, {geolocation_data['country']}")
                    break
        except Exception as e:
            logger.warning(f"Geolocation API error for {ip_address}: {e}")
            continue
    
    return geolocation_data

def get_network_info(client_ip):
    """Get additional network information about the client"""
    network_info = {}
    
    try:
        # Try to get hostname via reverse DNS
        try:
            hostname = socket.gethostbyaddr(client_ip)[0]
            network_info['hostname'] = hostname
        except:
            network_info['hostname'] = "unknown"
        
        # Try to get MAC address if on local network
        if client_ip.startswith(('192.168.', '10.', '172.')):
            mac_address = get_mac_from_arp(client_ip)
            network_info['mac_address'] = mac_address
        else:
            network_info['mac_address'] = "remote"
        
        # Get geolocation info (basic)
        network_info['is_local'] = client_ip.startswith(('192.168.', '10.', '172.', '127.'))
        
        # Get detailed geolocation
        network_info['geolocation'] = get_ip_geolocation(client_ip)
        
    except Exception as e:
        logger.error(f"Network info error: {e}")
        network_info = {
            'hostname': 'unknown', 
            'mac_address': 'unknown', 
            'is_local': False,
            'geolocation': get_ip_geolocation(client_ip)
        }
    
    return network_info

def get_mac_from_arp(ip):
    """Try to get MAC address from ARP table (works only on local network)"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if ip in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1].replace('-', ':')
        
        elif platform.system() in ["Linux", "Darwin"]:  # Darwin is macOS
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if ip in line and ':' in line:
                        parts = line.split()
                        for part in parts:
                            if ':' in part and len(part) == 17:  # MAC format
                                return part
    except:
        pass
    
    return "unknown"

def get_client_ip(request):
    """Get the real client IP address from request headers"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def serialize_headers(request_meta):
    """
    Safely serialize request.META headers, filtering out non-serializable objects
    """
    serializable_headers = {}
    
    # List of keys to exclude (Django-specific objects that can't be serialized)
    exclude_keys = [
        'wsgi.input', 'wsgi.errors', 'wsgi.file_wrapper'
    ]
    
    for key, value in request_meta.items():
        # Skip non-serializable keys
        if key in exclude_keys:
            continue
            
        # Try to serialize the value
        try:
            # Test if it's JSON serializable
            json.dumps(value)
            serializable_headers[key] = value
        except (TypeError, ValueError):
            # If not serializable, convert to string
            try:
                serializable_headers[key] = str(value)
            except:
                # If even string conversion fails, skip it
                serializable_headers[key] = f"<non-serializable {type(value).__name__}>"
    
    return serializable_headers

def log_to_text_file(log_data):
    """Log access to text file"""
    try:
        from django.utils import timezone
        import json
        
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {json.dumps(log_data, indent=2, default=str)}\n"
        
        with open(settings.TRACKING_LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Text file logging error: {e}")
