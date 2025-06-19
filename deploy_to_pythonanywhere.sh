#!/bin/bash
# deploy_to_pythonanywhere.sh - Automated deployment script

echo "🚀 Django Tracking Server - PythonAnywhere Deployment Script"
echo "============================================================="

# Configuration
PROJECT_NAME="tracking_project"
PYTHON_VERSION="3.10"
DOMAIN="tarekeissa.pythonanywhere.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_step() {
    echo -e "${BLUE}📋 Step $1: $2${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Setup project structure
log_step 1 "Setting up project structure"
cd /home/tracking/

if [ ! -d "$PROJECT_NAME" ]; then
    log_warning "Project directory doesn't exist. Please upload your files first."
    echo "Expected structure:"
    echo "/home/tracking/tracking_project/"
    echo "├── manage.py"
    echo "├── requirements.txt"
    echo "├── tracking_project/"
    echo "└── tracking_app/"
    exit 1
fi

cd $PROJECT_NAME
log_success "Project directory found"

# Step 2: Create virtual environment
log_step 2 "Creating virtual environment"
if [ ! -d "venv" ]; then
    python${PYTHON_VERSION} -m venv venv
    log_success "Virtual environment created"
else
    log_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
log_success "Virtual environment activated"

# Step 3: Install dependencies
log_step 3 "Installing dependencies"
pip install --upgrade pip
pip install django gunicorn whitenoise python-dotenv requests pillow
log_success "Dependencies installed"

# Step 4: Check Django setup
log_step 4 "Checking Django configuration"
if [ ! -f "manage.py" ]; then
    log_error "manage.py not found!"
    exit 1
fi

# Check if we can import Django
python -c "import django; print(f'Django version: {django.get_version()}')"
log_success "Django configuration OK"

# Step 5: Database setup
log_step 5 "Setting up database"
python manage.py makemigrations tracking_app
python manage.py migrate
log_success "Database migrations completed"

# Step 6: Collect static files
log_step 6 "Collecting static files"
python manage.py collectstatic --noinput
log_success "Static files collected"

# Step 7: Test Django
log_step 7 "Testing Django configuration"
python manage.py check --deploy
log_success "Django deployment check passed"

# Step 8: Create superuser (interactive)
log_step 8 "Creating superuser account"
echo "Please create a superuser account for the admin interface:"
python manage.py createsuperuser

log_success "Deployment script completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Go to PythonAnywhere Web tab"
echo "2. Create new web app: $DOMAIN"
echo "3. Set source code: /home/tracking/$PROJECT_NAME"
echo "4. Set virtual env: /home/tracking/$PROJECT_NAME/venv"
echo "5. Configure WSGI file (see guide)"
echo "6. Add static files mapping: /static/ → /home/tracking/$PROJECT_NAME/staticfiles/"
echo "7. Reload web app"
echo ""
echo "🌍 Your site will be available at: https://$DOMAIN"

# test_deployment.py - Test script for PythonAnywhere
cat > test_deployment.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Django deployment on PythonAnywhere
Run this after deployment to verify everything works
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tracking_project.settings')
django.setup()

from tracking_app.models import AccessLog
from tracking_app.utils import get_server_mac_address

def test_database():
    """Test database connection and operations"""
    print("🗄️  Testing database connection...")
    
    try:
        # Count existing logs
        count = AccessLog.objects.count()
        print(f"   ✅ Database connected. Current logs: {count}")
        
        # Create test log
        test_log = AccessLog.objects.create(
            ip_address='127.0.0.1',
            mac_address='test:mac:address',
            hostname='test-deployment',
            user_agent='DeploymentTestScript/1.0',
            request_path='/test_deployment',
            query_params={'test': True},
            server_mac=get_server_mac_address(),
            trigger_method='deployment_test',
            trigger_type='test_deployment'
        )
        
        print(f"   ✅ Test log created: ID {test_log.id}")
        
        # Clean up
        test_log.delete()
        print("   ✅ Test log cleaned up")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def test_endpoints():
    """Test web endpoints"""
    print("🌐 Testing web endpoints...")
    
    base_url = "https://tarekeissa.pythonanywhere.com"
    endpoints = [
        ('/', 'Home page'),
        ('/status/', 'Dashboard'),
        ('/map/', 'IP Map'),
        ('/admin/', 'Admin interface'),
        ('/track/?mac=test&method=deployment_test&trigger=endpoint_test', 'Tracking endpoint')
    ]
    
    for endpoint, description in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {description}: OK ({response.status_code})")
            elif response.status_code in [301, 302]:
                print(f"   ✅ {description}: Redirect ({response.status_code})")
            else:
                print(f"   ⚠️  {description}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {description}: Error - {e}")

def test_tracking_functionality():
    """Test the tracking functionality specifically"""
    print("🎯 Testing tracking functionality...")
    
    try:
        url = "https://tarekeissa.pythonanywhere.com/track/"
        params = {
            'mac': 'test:deployment:mac',
            'method': 'deployment_verification',
            'trigger': 'functionality_test',
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Tracking successful: {data.get('message')}")
                print(f"   📊 Database ID: {data.get('database_id')}")
                print(f"   💾 Database saved: {data.get('database_saved')}")
                return True
            else:
                print(f"   ❌ Tracking failed: {data}")
                return False
        else:
            print(f"   ❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Tracking test error: {e}")
        return False

def test_geolocation():
    """Test geolocation functionality"""
    print("🗺️  Testing geolocation...")
    
    try:
        from tracking_app.utils import get_ip_geolocation
        
        # Test with Google DNS IP
        result = get_ip_geolocation('8.8.8.8')
        
        if result and result.get('country') != 'Unknown':
            print(f"   ✅ Geolocation working: {result.get('city')}, {result.get('country')}")
            return True
        else:
            print(f"   ⚠️  Geolocation limited: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Geolocation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 PythonAnywhere Deployment Test Suite")
    print("=" * 50)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    results = {
        'database': test_database(),
        'endpoints': test_endpoints(),
        'tracking': test_tracking_functionality(),
        'geolocation': test_geolocation()
    }
    
    print("")
    print("📊 Test Results Summary:")
    print("=" * 30)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.capitalize()}: {status}")
    
    overall_success = all(results.values())
    
    print("")
    if overall_success:
        print("🎉 All tests passed! Your deployment is successful!")
        print("")
        print("🌍 Your tracking server is live at:")
        print("   https://tarekeissa.pythonanywhere.com/")
        print("")
        print("🎯 Ready to receive auto-triggers from your attack tools!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("💡 Refer to the troubleshooting guide for solutions.")
    
    print("")
    print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
EOF

echo "✅ Created test_deployment.py"

# quick_check.sh - Quick status check script
cat > quick_check.sh << 'EOF'
#!/bin/bash
# Quick deployment status check

echo "🔍 Quick Deployment Status Check"
echo "================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Not in Django project directory"
    echo "Run: cd /home/tracking/tracking_project"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

source venv/bin/activate

echo "📍 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "🎯 Django version: $(python -c 'import django; print(django.get_version())')"

# Check database
if [ -f "tracking_logs.db" ]; then
    echo "✅ Database file exists"
    echo "📊 Database size: $(ls -lh tracking_logs.db | awk '{print $5}')"
else
    echo "❌ Database file not found"
fi

# Check static files
if [ -d "staticfiles" ]; then
    echo "✅ Static files directory exists"
    echo "📁 Static files count: $(find staticfiles -type f | wc -l)"
else
    echo "❌ Static files not collected"
fi

# Check log files
if [ -f "django_tracking.log" ]; then
    echo "✅ Django log file exists"
    echo "📄 Log file size: $(ls -lh django_tracking.log | awk '{print $5}')"
    echo "📝 Recent log entries:"
    tail -5 django_tracking.log
else
    echo "⚠️  No Django log file yet"
fi

# Test Django
echo ""
echo "🧪 Testing Django..."
python manage.py check --quiet
if [ $? -eq 0 ]; then
    echo "✅ Django check passed"
else
    echo "❌ Django check failed"
fi

echo ""
echo "🌐 Test your deployment:"
echo "   https://tarekeissa.pythonanywhere.com/"
echo "   https://tarekeissa.pythonanywhere.com/track/?mac=test&method=test&trigger=test"
EOF

chmod +x quick_check.sh
echo "✅ Created quick_check.sh"

# Create requirements.txt with exact versions
cat > requirements.txt << 'EOF'
Django==4.2.7
gunicorn==21.2.0
whitenoise==6.6.0
python-dotenv==1.0.0
requests==2.31.0
Pillow==10.1.0
EOF

echo "✅ Created requirements.txt with pinned versions"

# Create .gitignore for the project
cat > .gitignore << 'EOF'
# Django
*.log
*.pot
*.pyc
__pycache__/
local_settings.py
db.sqlite3
db.sqlite3-journal

# Virtual environment
venv/
env/

# Static files
staticfiles/

# Logs
*.log
django_tracking.log*
enhanced_ip_log.txt

# Database
tracking_logs.db*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backup files
*_backup*
*.bak

# Environment variables
.env
.env.local
.env.production

# Cache
django_cache/
*.cache
EOF

echo "✅ Created .gitignore"

echo ""
echo "🎯 Deployment files created:"
echo "   ✅ deploy_to_pythonanywhere.sh - Main deployment script"
echo "   ✅ test_deployment.py - Comprehensive test suite"  
echo "   ✅ quick_check.sh - Quick status check"
echo "   ✅ requirements.txt - Dependencies with versions"
echo "   ✅ .gitignore - Git ignore rules"
echo ""
echo "🚀 To deploy:"
echo "   1. Upload files to /home/tracking/tracking_project/"
echo "   2. Run: bash deploy_to_pythonanywhere.sh"
echo "   3. Configure web app in PythonAnywhere dashboard"
echo "   4. Run: python test_deployment.py"
echo ""
echo "📖 Full guide: See the complete deployment documentation above"