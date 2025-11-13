#!/bin/bash

################################################################################
# FlooorGang Scanner - Raspberry Pi Automated Setup Script
################################################################################
#
# This script automates the installation of the FlooorGang scanner on a
# Raspberry Pi. Run this after completing the initial OS setup.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/flooorgang/main/setup_pi.sh | bash
#   or
#   wget -O - https://raw.githubusercontent.com/YOUR_USERNAME/flooorgang/main/setup_pi.sh | bash
#   or (if already cloned)
#   bash setup_pi.sh
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="flooorgang"
INSTALL_DIR="$HOME/$PROJECT_NAME"
PYTHON_VERSION="3.11"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

################################################################################
# Pre-flight Checks
################################################################################

print_header "FlooorGang Scanner - Raspberry Pi Setup"

print_info "Checking system requirements..."

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    print_warning "Not running on a Raspberry Pi, but continuing anyway..."
else
    PI_MODEL=$(cat /proc/device-tree/model)
    print_info "Detected: $PI_MODEL"
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root (no sudo)"
    exit 1
fi

# Check internet connectivity
if ! ping -c 1 google.com &> /dev/null; then
    print_error "No internet connection detected"
    exit 1
fi
print_success "Internet connection OK"

################################################################################
# System Update
################################################################################

print_header "Step 1: Updating System Packages"

print_info "This may take 10-15 minutes on first run..."
sudo apt update
sudo apt upgrade -y
print_success "System packages updated"

################################################################################
# Install System Dependencies
################################################################################

print_header "Step 2: Installing System Dependencies"

print_info "Installing Python and build tools..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    build-essential \
    libatlas-base-dev \
    libopenjp2-7 \
    libtiff5 \
    libfreetype6-dev \
    python3-tk \
    fontconfig \
    fonts-roboto

print_success "System dependencies installed"

# Check Python version
PYTHON_CURRENT=$(python3 --version | awk '{print $2}')
print_info "Current Python version: $PYTHON_CURRENT"

################################################################################
# Clone Repository
################################################################################

print_header "Step 3: Cloning FlooorGang Repository"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "Directory $INSTALL_DIR already exists"
    read -p "Do you want to remove it and re-clone? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        print_info "Removed existing directory"
    else
        print_info "Skipping clone, using existing directory"
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    print_info "Cloning repository..."
    git clone https://github.com/YOUR_USERNAME/flooorgang.git "$INSTALL_DIR"
    print_success "Repository cloned to $INSTALL_DIR"
else
    cd "$INSTALL_DIR"
    print_info "Pulling latest changes..."
    git pull origin main
    print_success "Repository updated"
fi

cd "$INSTALL_DIR"

################################################################################
# Create Virtual Environment
################################################################################

print_header "Step 4: Setting Up Python Virtual Environment"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        print_info "Removed existing virtual environment"
    fi
fi

if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

print_info "Activating virtual environment..."
source venv/bin/activate

print_info "Upgrading pip..."
pip install --upgrade pip

################################################################################
# Install Python Dependencies
################################################################################

print_header "Step 5: Installing Python Dependencies"

print_info "This may take 10-20 minutes on first install..."
pip install -r requirements.txt
print_success "Python dependencies installed"

################################################################################
# Configure Environment Variables
################################################################################

print_header "Step 6: Configuring Environment Variables"

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning ".env file created from template"
        print_warning "You MUST edit .env with your actual API keys"
        print_info "Run: nano $INSTALL_DIR/.env"
    else
        print_error ".env.example not found"
        print_info "Creating basic .env template..."
        cat > .env << EOF
# The Odds API
ODDS_API_KEY=your_odds_api_key_here

# Twitter API (optional for now)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
EOF
        print_success "Basic .env template created"
    fi
else
    print_success ".env file already exists"
fi

################################################################################
# Create Directories
################################################################################

print_header "Step 7: Creating Required Directories"

mkdir -p logs
mkdir -p graphics
print_success "Created logs and graphics directories"

################################################################################
# Setup Execution Script
################################################################################

print_header "Step 8: Creating Execution Script"

cat > run_scanner.sh << 'EOF'
#!/bin/bash

# FlooorGang Scanner - Automated Execution Script
# Runs daily at 12:00 PM ET to analyze NBA games

# Configuration
PROJECT_DIR="$HOME/flooorgang"
VENV_PATH="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/scanner_$(date +%Y%m%d_%H%M%S).log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Start logging
echo "================================================" | tee -a "$LOG_FILE"
echo "FlooorGang Scanner Run - $(date)" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || {
    echo "ERROR: Could not change to project directory" | tee -a "$LOG_FILE"
    exit 1
}

# Activate virtual environment
source "$VENV_PATH/bin/activate" || {
    echo "ERROR: Could not activate virtual environment" | tee -a "$LOG_FILE"
    exit 1
}

# Run the scanner
echo "Starting scanner..." | tee -a "$LOG_FILE"
python src/scanner_v2.py 2>&1 | tee -a "$LOG_FILE"

# Capture exit code
EXIT_CODE=$?

# Log completion
echo "================================================" | tee -a "$LOG_FILE"
echo "Scanner completed with exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"

# Keep only last 30 days of logs
find "$LOG_DIR" -name "scanner_*.log" -mtime +30 -delete

# Exit with the scanner's exit code
exit $EXIT_CODE
EOF

chmod +x run_scanner.sh
print_success "Execution script created and made executable"

################################################################################
# Test Installation (Optional)
################################################################################

print_header "Step 9: Installation Complete!"

print_success "FlooorGang scanner installed successfully!"
echo ""
print_info "Installation location: $INSTALL_DIR"
print_info "Virtual environment: $INSTALL_DIR/venv"
print_info "Execution script: $INSTALL_DIR/run_scanner.sh"
echo ""

print_warning "IMPORTANT: Next Steps"
echo ""
echo "1. Configure your API keys:"
echo "   nano $INSTALL_DIR/.env"
echo ""
echo "2. Test the scanner manually:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo "   python src/scanner_v2.py"
echo ""
echo "3. Set up automated daily runs:"
echo "   crontab -e"
echo "   Add this line:"
echo "   0 12 * * * $INSTALL_DIR/run_scanner.sh"
echo ""

read -p "Would you like to test the installation now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_header "Testing Installation"

    if ! grep -q "your_odds_api_key_here" .env; then
        print_info "Running scanner test..."
        source venv/bin/activate
        python src/scanner_v2.py
        print_success "Test complete! Check output above for any errors."
    else
        print_error "Please configure .env file first"
        print_info "Run: nano $INSTALL_DIR/.env"
    fi
else
    print_info "Skipping test. Run manually when ready:"
    print_info "  cd $INSTALL_DIR && ./run_scanner.sh"
fi

print_header "Setup Complete!"
print_success "FlooorGang scanner is ready to use!"
