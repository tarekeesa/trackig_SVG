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

# tracking_app/views.py - Updated with geolocation and map view
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
import json
import base64
import logging
from .models import AccessLog
from .utils import get_server_mac_address, get_network_info, get_client_ip, log_to_text_file, serialize_headers

logger = logging.getLogger('tracking_app')

@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def track_endpoint(request):
    """Enhanced tracking endpoint for auto-triggers"""
    
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    client_ip = get_client_ip(request)
    timestamp = timezone.now()
    
    # Get query parameters
    query_params = dict(request.GET)
    
    print(f"\n🎯 AUTO-TRIGGER DETECTED!")
    print(f"⏰ Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"📍 IP: {client_ip}")
    
    # Get comprehensive client information (now includes geolocation)
    network_info = get_network_info(client_ip)
    
    # Safely serialize headers
    safe_headers = serialize_headers(request.META)
    
    # Collect all available data
    log_data = {
        'timestamp': timestamp.isoformat(),
        'ip_address': client_ip,
        'client_mac': query_params.get('mac', ['unknown'])[0] if 'mac' in query_params else 'unknown',
        'detected_mac': network_info.get('mac_address', 'unknown'),
        'hostname': network_info.get('hostname', 'unknown'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'referer': request.META.get('HTTP_REFERER', 'None'),
        'request_path': request.get_full_path(),
        'query_params': query_params,
        'server_mac': get_server_mac_address(),
        'is_local_network': network_info.get('is_local', False),
        'headers': safe_headers,
        'method': query_params.get('method', ['unknown'])[0] if 'method' in query_params else 'unknown',
        'trigger': query_params.get('trigger', ['unknown'])[0] if 'trigger' in query_params else 'unknown',
        'format': query_params.get('format', ['json'])[0] if 'format' in query_params else 'json',
        'via_ngrok': 'ngrok' in request.META.get('HTTP_HOST', '').lower(),
        'geolocation': network_info.get('geolocation', {})
    }
    
    # Enhanced console output with trigger analysis
    trigger_type = log_data['trigger']
    method_type = log_data['method']
    
    # Create AccessLog entry
    access_log = None
    try:
        access_log = AccessLog.objects.create(
            ip_address=client_ip,
            mac_address=log_data['client_mac'],
            hostname=log_data['hostname'],
            user_agent=log_data['user_agent'],
            referer=log_data['referer'] if log_data['referer'] != 'None' else None,
            request_path=log_data['request_path'],
            query_params=query_params,
            server_mac=log_data['server_mac'],
            geolocation=log_data['geolocation'],  # Now includes detailed geolocation
            trigger_method=method_type,
            trigger_type=trigger_type,
            headers=safe_headers,
            is_local_network=log_data['is_local_network'],
            via_ngrok=log_data['via_ngrok'],
            response_format=log_data['format']
        )
        
        trigger_category = access_log.trigger_category
        print(f"✅ Database entry created: ID {access_log.id}")
        
    except Exception as e:
        logger.error(f"Database logging error: {e}")
        trigger_category = "⚡ AUTO-TRIGGER"
        print(f"❌ Database logging failed: {e}")
    
    print(f"🎯 Type: {trigger_category}")
    print(f"⚙️ Method: {method_type}")
    print(f"🎭 Trigger: {trigger_type}")
    print(f"💻 Client MAC: {log_data['client_mac']}")
    print(f"🔍 Detected MAC: {log_data['detected_mac']}")
    print(f"🏠 Hostname: {log_data['hostname']}")
    print(f"🌐 User Agent: {log_data['user_agent'][:60]}...")
    print(f"📡 Server MAC: {log_data['server_mac']}")
    print(f"🏢 Network: {'Local' if log_data['is_local_network'] else 'Remote'}")
    print(f"🌍 Via Ngrok: {'Yes' if log_data['via_ngrok'] else 'No'}")
    
    # Print geolocation info
    geo = log_data['geolocation']
    if geo and not geo.get('is_local'):
        print(f"🗺️ Location: {geo.get('city', 'Unknown')}, {geo.get('country', 'Unknown')}")
        print(f"📍 Coordinates: {geo.get('latitude', 0)}, {geo.get('longitude', 0)}")
        print(f"🏢 ISP: {geo.get('isp', 'Unknown')}")
    
    if query_params.get('host'):
        print(f"💾 Client Host: {query_params['host'][0]}")
    
    if query_params.get('coords'):
        print(f"📐 Coordinates: {query_params['coords'][0]}")
    
    # Log to text file as well
    log_to_text_file(log_data)
    
    # Handle different response formats
    if log_data['format'] == 'image':
        print(f"🖼️ Returning 1x1 tracking pixel")
        
        # Return a 1x1 transparent PNG pixel
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        response = HttpResponse(png_data, content_type='image/png')
        response['Content-Length'] = str(len(png_data))
        
    elif log_data['format'] == 'css':
        print(f"🎨 Returning CSS tracking response")
        
        css_data = "/* Auto-tracking CSS loaded successfully */"
        response = HttpResponse(css_data, content_type='text/css')
        
    else:
        # Send enhanced JSON response
        response_data = {
            'status': 'auto_trigger_logged',
            'timestamp': timestamp.isoformat(),
            'tracking_id': f"auto_{int(timestamp.timestamp())}",
            'message': 'AUTO-TRIGGER successfully logged!',
            'method': log_data['method'],
            'trigger': log_data['trigger'],
            'trigger_category': trigger_category,
            'via_ngrok': log_data['via_ngrok'],
            'geolocation': log_data['geolocation'],
            'success': True,
            'database_id': access_log.id if access_log else None,
            'database_saved': access_log is not None
        }
        
        response = JsonResponse(response_data, json_dumps_params={'indent': 2})
    
    print(f"✅ AUTO-TRIGGER LOGGED SUCCESSFULLY!")
    print("=" * 60)
    
    return response

def map_view(request):
    """Interactive map view showing IP locations"""
    try:
        # Get all logs with geolocation data
        logs_with_geo = AccessLog.objects.exclude(
            geolocation__isnull=True
        ).exclude(
            geolocation__exact={}
        ).order_by('-timestamp')
        
        # Prepare map data
        map_data = []
        ip_stats = {}
        
        for log in logs_with_geo:
            geo = log.geolocation
            if not geo or geo.get('is_local', False):
                continue
                
            lat = geo.get('latitude', 0)
            lng = geo.get('longitude', 0)
            
            if lat == 0 and lng == 0:
                continue
            
            ip = log.ip_address
            
            # Aggregate data by IP
            if ip not in ip_stats:
                ip_stats[ip] = {
                    'ip': ip,
                    'latitude': lat,
                    'longitude': lng,
                    'city': geo.get('city', 'Unknown'),
                    'country': geo.get('country', 'Unknown'),
                    'country_code': geo.get('country_code', 'UNK'),
                    'region': geo.get('region', 'Unknown'),
                    'isp': geo.get('isp', 'Unknown'),
                    'timezone': geo.get('timezone', 'Unknown'),
                    'count': 0,
                    'first_seen': log.timestamp,
                    'last_seen': log.timestamp,
                    'triggers': [],
                    'methods': set(),
                    'via_ngrok': log.via_ngrok,
                    'hostname': log.hostname,
                    'user_agents': set()
                }
            
            # Update stats
            stats = ip_stats[ip]
            stats['count'] += 1
            stats['last_seen'] = max(stats['last_seen'], log.timestamp)
            stats['first_seen'] = min(stats['first_seen'], log.timestamp)
            stats['triggers'].append({
                'type': log.trigger_type,
                'method': log.trigger_method,
                'timestamp': log.timestamp.isoformat(),
                'category': log.trigger_category
            })
            stats['methods'].add(log.trigger_method or 'unknown')
            if log.user_agent:
                stats['user_agents'].add(log.user_agent[:50])  # Truncate for display
        
        # Convert to list and sort by count
        map_data = list(ip_stats.values())
        for item in map_data:
            item['methods'] = list(item['methods'])
            item['user_agents'] = list(item['user_agents'])
        
        map_data.sort(key=lambda x: x['count'], reverse=True)
        
        context = {
            'map_data': json.dumps(map_data, default=str),
            'total_ips': len(map_data),
            'total_triggers': sum(item['count'] for item in map_data),
            'countries': len(set(item['country'] for item in map_data)),
            'server_mac': get_server_mac_address(),
            'current_time': timezone.now(),
        }
        
        return render(request, 'tracking_app/map.html', context)
        
    except Exception as e:
        logger.error(f"Map view error: {e}")
        return render(request, 'tracking_app/error.html', {'error': str(e)})

def status_dashboard(request):
    """Enhanced status dashboard with trigger analytics"""
    try:
        # Get statistics
        total_logs = AccessLog.objects.count()
        
        # Get trigger type breakdown
        trigger_stats = AccessLog.objects.values('trigger_type').annotate(
            count=Count('trigger_type')
        ).order_by('-count')[:10]
        
        # Get method breakdown
        method_stats = AccessLog.objects.values('trigger_method').annotate(
            count=Count('trigger_method')
        ).order_by('-count')[:10]
        
        # Get recent logs
        recent_logs = AccessLog.objects.select_related().order_by('-timestamp')[:20]
        
        # Get hourly activity for today
        hourly_stats = AccessLog.objects.filter(
            timestamp__date=timezone.now().date()
        ).extra(
            select={'hour': 'strftime("%%H", timestamp)'}
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        # Get top IPs
        top_ips = AccessLog.objects.values('ip_address').annotate(
            count=Count('ip_address')
        ).order_by('-count')[:10]
        
        # Get country stats
        country_stats = AccessLog.objects.exclude(
            geolocation__isnull=True
        ).exclude(
            geolocation__exact={}
        ).extra(
            select={'country': "JSON_EXTRACT(geolocation, '$.country')"}
        ).values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        context = {
            'total_logs': total_logs,
            'trigger_stats': trigger_stats,
            'method_stats': method_stats,
            'recent_logs': recent_logs,
            'hourly_stats': hourly_stats,
            'top_ips': top_ips,
            'country_stats': country_stats,
            'server_mac': get_server_mac_address(),
            'current_time': timezone.now(),
            'js_triggers': AccessLog.objects.filter(trigger_type__contains='js_').count(),
            'svg_triggers': AccessLog.objects.filter(trigger_type__contains='svg_').count(),
            'html_triggers': AccessLog.objects.filter(trigger_type__contains='html_').count(),
            'grid_triggers': AccessLog.objects.filter(trigger_type__contains='grid_').count(),
        }
        
        return render(request, 'tracking_app/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render(request, 'tracking_app/error.html', {'error': str(e)})

def logs_api(request):
    """API endpoint for logs with pagination and filtering"""
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 50)), 100)  # Max 100 per page
        trigger_type = request.GET.get('trigger_type')
        method = request.GET.get('method')
        ip_filter = request.GET.get('ip')
        
        # Build queryset
        queryset = AccessLog.objects.all()
        
        if trigger_type:
            queryset = queryset.filter(trigger_type__icontains=trigger_type)
        if method:
            queryset = queryset.filter(trigger_method__icontains=method)
        if ip_filter:
            queryset = queryset.filter(ip_address__icontains=ip_filter)
        
        # Paginate
        paginator = Paginator(queryset.order_by('-timestamp'), per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize logs
        logs_data = []
        for log in page_obj:
            log_data = {
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'ip': log.ip_address,
                'mac': log.mac_address,
                'hostname': log.hostname,
                'user_agent': log.user_agent,
                'referer': log.referer,
                'path': log.request_path,
                'query_params': log.query_params,
                'server_mac': log.server_mac,
                'geolocation': log.geolocation,
                'trigger_method': log.trigger_method,
                'trigger_type': log.trigger_type,
                'trigger_category': log.trigger_category,
                'is_local_network': log.is_local_network,
                'via_ngrok': log.via_ngrok,
                'response_format': log.response_format,
            }
            logs_data.append(log_data)
        
        response_data = {
            'total_logs': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'timestamp': timezone.now().isoformat(),
            'logs': logs_data
        }
        
        return JsonResponse(response_data, json_dumps_params={'indent': 2})
        
    except Exception as e:
        logger.error(f"Logs API error: {e}")
        return JsonResponse({
            'error': f"Error retrieving logs: {e}",
            'timestamp': timezone.now().isoformat()
        }, status=500)

def home_view(request):
    """Home page with server information"""
    try:
        context = {
            'server_mac': get_server_mac_address(),
            'current_time': timezone.now(),
            'total_logs': AccessLog.objects.count(),
            'recent_logs': AccessLog.objects.order_by('-timestamp')[:5],
        }
        return render(request, 'tracking_app/home.html', context)
    except Exception as e:
        logger.error(f"Home view error: {e}")
        return render(request, 'tracking_app/error.html', {'error': str(e)})

