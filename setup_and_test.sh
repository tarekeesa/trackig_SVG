#!/bin/bash
# setup_and_test.sh - Database Setup and Testing Script

echo "🚀 Django Auto-Trigger Tracking Server Setup"
echo "============================================="

# Step 1: Make migrations
echo "📦 Creating database migrations..."
python manage.py makemigrations tracking_app

# Step 2: Apply migrations
echo "🔧 Applying database migrations..."
python manage.py migrate

# Step 3: Create superuser (optional)
echo "👤 Create superuser? (y/n)"
read -r create_user
if [ "$create_user" = "y" ]; then
    python manage.py createsuperuser
fi

# Step 4: Test the server
echo "🧪 Starting test server..."
echo "Server will start on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server in background
python manage.py runserver &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

echo "✅ Server started! Testing endpoints..."

# Test basic tracking endpoint
echo "🎯 Testing tracking endpoint..."
curl -s "http://127.0.0.1:8000/track/?mac=test&method=test&trigger=test" | python -m json.tool

echo ""
echo "📊 Testing dashboard..."
curl -s -I "http://127.0.0.1:8000/status/" | head -n 1

echo ""
echo "📜 Testing logs API..."
curl -s "http://127.0.0.1:8000/logs/" | python -c "import sys, json; data=json.load(sys.stdin); print(f'Total logs: {data[\"total_logs\"]}')"

echo ""
echo "🎉 Setup complete! Available endpoints:"
echo "   🏠 Home: http://127.0.0.1:8000/"
echo "   🎯 Track: http://127.0.0.1:8000/track/"
echo "   📊 Dashboard: http://127.0.0.1:8000/status/"
echo "   📜 Logs: http://127.0.0.1:8000/logs/"
echo "   ⚙️ Admin: http://127.0.0.1:8000/admin/"

echo ""
echo "Press Enter to stop the test server..."
read -r
kill $SERVER_PID

# Python test script
cat > test_tracking.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Django tracking server
"""
import requests
import json
import time

def test_tracking_endpoint():
    """Test the tracking endpoint with various parameters"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Django Tracking Server")
    print("=" * 40)
    
    # Test 1: Basic tracking
    print("1. Testing basic tracking...")
    response = requests.get(f"{base_url}/track/", params={
        'mac': 'test:mac:addr',
        'method': 'svg_injection',
        'trigger': 'svg_inject_immediate',
        'demo': 'test'
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: {data.get('message')}")
        print(f"   📊 Database ID: {data.get('database_id')}")
        print(f"   💾 Database Saved: {data.get('database_saved')}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 2: Image format
    print("\n2. Testing image format...")
    response = requests.get(f"{base_url}/track/", params={
        'mac': 'test:mac:addr',
        'method': 'image_beacon',
        'trigger': 'invisible_pixel',
        'format': 'image'
    })
    
    if response.status_code == 200 and response.headers.get('content-type') == 'image/png':
        print(f"   ✅ Success: Image pixel returned")
        print(f"   📏 Size: {len(response.content)} bytes")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 3: Multiple rapid requests (like real auto-triggers)
    print("\n3. Testing rapid fire requests...")
    for i in range(5):
        response = requests.get(f"{base_url}/track/", params={
            'mac': 'test:mac:rapid',
            'method': 'rapid_fire',
            'trigger': f'rapid_{i}',
            'sequence': i
        })
        if response.status_code == 200:
            print(f"   ✅ Rapid {i}: Success")
        else:
            print(f"   ❌ Rapid {i}: Failed")
        time.sleep(0.1)  # Small delay between requests
    
    # Test 4: Check logs API
    print("\n4. Testing logs API...")
    response = requests.get(f"{base_url}/logs/")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: {data.get('total_logs')} total logs")
        print(f"   📄 Current page: {data.get('current_page')}")
        print(f"   📊 Logs in response: {len(data.get('logs', []))}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 5: Dashboard
    print("\n5. Testing dashboard...")
    response = requests.get(f"{base_url}/status/")
    
    if response.status_code == 200:
        print(f"   ✅ Success: Dashboard loaded")
        print(f"   📏 Size: {len(response.content)} bytes")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    print("\n🎉 Testing complete!")
    print("\nNext steps:")
    print("1. Check the dashboard: http://127.0.0.1:8000/status/")
    print("2. View logs: http://127.0.0.1:8000/logs/")
    print("3. Access admin: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    try:
        test_tracking_endpoint()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server")
        print("Make sure the Django server is running:")
        print("python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")
EOF

echo ""
echo "📝 Created test_tracking.py script"
echo "Run it with: python test_tracking.py"