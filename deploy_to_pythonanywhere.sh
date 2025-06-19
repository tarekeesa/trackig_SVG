#!/bin/bash
# deploy_to_pythonanywhere.sh - Automated deployment script for PythonAnywhere

echo "🚀 Django Tracking Server - PythonAnywhere Deployment Script"
echo "============================================================="

# Configuration - Update these for your account
USERNAME="tarekeissa"  # Replace with your PythonAnywhere username
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

# Check if we're on PythonAnywhere
if [[ ! -d "/home/$USERNAME" ]]; then
    log_error "This script must be run on PythonAnywhere!"
    echo "Current directory: $(pwd)"
    echo "Please run this script in a PythonAnywhere Bash console."
    exit 1
fi

# Step 1: Setup project structure
log_step 1 "Setting up project structure"
cd /home/$USERNAME/

if [ ! -d "$PROJECT_NAME" ]; then
    log_error "Project directory doesn't exist: /home/$USERNAME/$PROJECT_NAME"
    echo "Please upload your Django project files first."
    echo ""
    echo "Expected structure:"
    echo "/home/$USERNAME/$PROJECT_NAME/"
    echo "├── manage.py"
    echo "├── requirements.txt"
    echo "├── tracking_project/"
    echo "└── tracking_app/"
    exit 1
fi

cd $PROJECT_NAME
log_success "Project directory found: $(pwd)"

# Step 2: Create virtual environment
log_step 2 "Creating virtual environment"
if [ ! -d "venv" ]; then
    python${PYTHON_VERSION} -m venv venv
    if [ $? -eq 0 ]; then
        log_success "Virtual environment created"
    else
        log_error "Failed to create virtual environment"
        exit 1
    fi
else
    log_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -eq 0 ]; then
    log_success "Virtual environment activated"
else
    log_error "Failed to activate virtual environment"
    exit 1
fi

# Step 3: Install dependencies
log_step 3 "Installing dependencies"
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    log_success "Dependencies installed from requirements.txt"
else
    pip install django gunicorn whitenoise python-dotenv requests pillow
    log_success "Basic dependencies installed"
fi

# Step 4: Check Django setup
log_step 4 "Checking Django configuration"
if [ ! -f "manage.py" ]; then
    log_error "manage.py not found in $(pwd)!"
    echo "Files in current directory:"
    ls -la
    exit 1
fi

# Check if we can import Django
python -c "import django; print(f'Django version: {django.get_version()}')"
if [ $? -eq 0 ]; then
    log_success "Django configuration OK"
else
    log_error "Django import failed"
    exit 1
fi

# Step 5: Database setup
log_step 5 "Setting up database"
python manage.py makemigrations tracking_app
python manage.py migrate
if [ $? -eq 0 ]; then
    log_success "Database migrations completed"
else
    log_error "Database migration failed"
    exit 1
fi

# Step 6: Collect static files
log_step 6 "Collecting static files"
python manage.py collectstatic --noinput
if [ $? -eq 0 ]; then
    log_success "Static files collected"
else
    log_warning "Static files collection had issues (this might be OK)"
fi

# Step 7: Test Django
log_step 7 "Testing Django configuration"
python manage.py check --deploy
if [ $? -eq 0 ]; then
    log_success "Django deployment check passed"
else
    log_warning "Django deployment check had warnings (check output above)"
fi

# Step 8: Create superuser (optional)
log_step 8 "Creating superuser account"
echo "Do you want to create a superuser account now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
    log_success "Superuser created"
else
    log_warning "Skipping superuser creation (you can run 'python manage.py createsuperuser' later)"
fi

log_success "Deployment script completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Go to PythonAnywhere Web tab: https://www.pythonanywhere.com/user/$USERNAME/webapps/"
echo "2. Create new web app: $DOMAIN"
echo "3. Choose 'Manual configuration' and Python $PYTHON_VERSION"
echo "4. Set source code: /home/$USERNAME/$PROJECT_NAME"
echo "5. Set virtual env: /home/$USERNAME/$PROJECT_NAME/venv"
echo "6. Configure WSGI file (replace contents with provided code)"
echo "7. Add static files mapping: /static/ → /home/$USERNAME/$PROJECT_NAME/staticfiles/"
echo "8. Reload web app"
echo ""
echo "🌍 Your site will be available at: https://$DOMAIN"
echo ""
echo "📋 WSGI Configuration:"
echo "Replace the contents of your WSGI file with:"
echo "----------------------------------------"
echo "import os"
echo "import sys"
echo ""
echo "path = '/home/$USERNAME/$PROJECT_NAME'"
echo "if path not in sys.path:"
echo "    sys.path.insert(0, path)"
echo ""
echo "os.environ['DJANGO_SETTINGS_MODULE'] = 'tracking_project.settings'"
echo ""
echo "from django.core.wsgi import get_wsgi_application"
echo "application = get_wsgi_application()"
echo "----------------------------------------"