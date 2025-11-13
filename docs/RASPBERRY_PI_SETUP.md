# Raspberry Pi Setup Guide - FlooorGang Scanner

Complete guide to deploy the NBA betting scanner on your Raspberry Pi for automated daily execution.

## Why Raspberry Pi?

- **Residential IP**: NBA.com blocks cloud provider IPs (AWS, Railway, DigitalOcean), but residential IPs work fine
- **Zero hosting costs**: ~$0.50/month in electricity vs $6-40/month for cloud hosting
- **Always-on**: Reliable automated execution without keeping your laptop running
- **Scalable**: Can add NFL/MLB scanners without additional hosting fees

## Hardware Requirements

### What You Need
- Raspberry Pi 4 (2GB RAM minimum, 4GB+ recommended)
- MicroSD card (16GB minimum, 32GB+ recommended, Class 10)
- Power supply (USB-C, 5V/3A official adapter recommended)
- Ethernet cable (recommended) or WiFi
- HDMI cable + monitor (for initial setup only)
- USB keyboard (for initial setup only)

### Optional But Helpful
- Case with cooling fan
- Heat sinks
- SD card reader for your laptop

## Part 1: Initial Raspberry Pi Setup

### Step 1: Install Raspberry Pi OS

1. **Download Raspberry Pi Imager**
   - Go to: https://www.raspberrypi.com/software/
   - Install on your Mac/Windows computer

2. **Flash the OS**
   - Insert microSD card into your computer
   - Open Raspberry Pi Imager
   - Choose OS: "Raspberry Pi OS (64-bit)" (recommended) or "Raspberry Pi OS Lite" (headless)
   - Choose Storage: Select your microSD card
   - Click the gear icon ⚙️ for Advanced Options:
     - Set hostname: `flooorgang-pi`
     - Enable SSH: ✅ (use password authentication)
     - Set username: `pi` (or your choice)
     - Set password: [choose a secure password]
     - Configure WiFi (if using wireless):
       - SSID: [your WiFi name]
       - Password: [your WiFi password]
       - Country: US (or your country)
     - Set locale settings: America/Los_Angeles (or your timezone)
   - Click "WRITE" and wait for completion

3. **Boot the Pi**
   - Insert the microSD card into the Raspberry Pi
   - Connect ethernet cable (if using wired)
   - Connect HDMI to monitor (optional if SSH configured)
   - Connect keyboard (optional if SSH configured)
   - Connect power supply (Pi will boot automatically)
   - Wait 1-2 minutes for first boot

### Step 2: Connect to Your Pi

**Option A: Direct connection (monitor + keyboard)**
```bash
# Login with the username/password you set
# Username: pi
# Password: [your password]
```

**Option B: SSH from your Mac (recommended)**
```bash
# Find your Pi's IP address
# Check your router admin page, or use:
ping flooorgang-pi.local

# SSH into the Pi
ssh pi@flooorgang-pi.local
# or
ssh pi@[IP_ADDRESS]

# Enter the password you set during setup
```

### Step 3: Update System

```bash
# Update package lists and upgrade all packages
sudo apt update && sudo apt upgrade -y

# This may take 10-15 minutes on first run
```

### Step 4: Configure System (Optional but Recommended)

```bash
# Open Raspberry Pi configuration
sudo raspi-config

# Recommended settings:
# 1. System Options > Boot / Auto Login > Console (no auto-login)
# 2. Performance Options > GPU Memory > 16 (we don't need GPU for this)
# 3. Localisation Options > Timezone > [Your timezone]
# 4. Advanced Options > Expand Filesystem (if not already done)

# Exit and reboot
sudo reboot
```

## Part 2: Install FlooorGang Scanner

### Step 5: Install Python and Dependencies

```bash
# SSH back into the Pi after reboot
ssh pi@flooorgang-pi.local

# Install Python 3.11+ (Raspberry Pi OS usually has 3.9, we need newer)
sudo apt install -y python3 python3-pip python3-venv git

# Check Python version
python3 --version

# If version is less than 3.11, install from deadsnakes PPA:
# (Skip this if you have 3.11+)
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install system dependencies for matplotlib and other packages
sudo apt install -y \
  libatlas-base-dev \
  libopenjp2-7 \
  libtiff5 \
  libfreetype6-dev \
  python3-tk
```

### Step 6: Clone Repository and Setup

```bash
# Navigate to home directory
cd ~

# Clone the flooorgang repository
git clone https://github.com/YOUR_USERNAME/flooorgang.git
cd flooorgang

# Create virtual environment (use python3.11 if you installed it)
python3 -m venv venv
# or if you installed 3.11 specifically:
# python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# This may take 10-20 minutes on first install
```

### Step 7: Configure Environment Variables

```bash
# Create .env file from template
cp .env.example .env

# Edit the .env file with your credentials
nano .env

# Add your actual values:
# ODDS_API_KEY=your_actual_api_key_here
# TWITTER_API_KEY=your_twitter_api_key
# TWITTER_API_SECRET=your_twitter_secret
# TWITTER_ACCESS_TOKEN=your_access_token
# TWITTER_ACCESS_SECRET=your_access_secret
# SUPABASE_URL=your_supabase_project_url
# SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# Save: Ctrl+O, Enter, Ctrl+X
```

### Step 8: Test Scanner

```bash
# Make sure you're in the flooorgang directory with venv activated
cd ~/flooorgang
source venv/bin/activate

# Run a test scan
python src/scanner_v2.py

# You should see:
# - Player analysis output
# - Team analysis output
# - Picks found
# - Database save confirmation
# - Graphics generated

# Check the generated graphic
ls -la graphics/

# If everything works, you're ready for automation!
```

## Part 3: Automated Daily Execution

### Step 9: Create Execution Script

We'll create a wrapper script that handles logging and error reporting.

```bash
# Create the script
nano ~/flooorgang/run_scanner.sh
```

Paste this content:

```bash
#!/bin/bash

# FlooorGang Scanner - Automated Execution Script
# Runs daily at 12:00 PM ET to analyze NBA games

# Configuration
PROJECT_DIR="/home/pi/flooorgang"
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
```

Save and make executable:

```bash
# Save: Ctrl+O, Enter, Ctrl+X

# Make script executable
chmod +x ~/flooorgang/run_scanner.sh

# Test the script
~/flooorgang/run_scanner.sh

# Check the log
ls -la ~/flooorgang/logs/
tail -f ~/flooorgang/logs/scanner_*.log
```

### Step 10: Setup Cron Job

```bash
# Edit crontab
crontab -e

# If prompted, choose nano (option 1)

# Add this line at the bottom:
# Run scanner daily at 12:00 PM ET (noon)
0 12 * * * /home/pi/flooorgang/run_scanner.sh

# Note: This assumes your Pi timezone is set to ET
# To check timezone: timedatectl
# To change timezone: sudo timedatectl set-timezone America/New_York

# Save and exit: Ctrl+O, Enter, Ctrl+X
```

**Verify cron job:**
```bash
# List cron jobs
crontab -l

# Check cron is running
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog | tail -20
```

## Part 4: Monitoring and Maintenance

### Daily Monitoring

**Check if scanner ran today:**
```bash
# View recent logs
ls -lt ~/flooorgang/logs/ | head -5

# View today's log
tail -100 ~/flooorgang/logs/scanner_$(date +%Y%m%d)*.log

# Check for errors
grep -i error ~/flooorgang/logs/scanner_$(date +%Y%m%d)*.log
```

**Check generated graphics:**
```bash
# List recent graphics
ls -lt ~/flooorgang/graphics/ | head -5
```

**View database entries:**
```bash
# You can check your Supabase dashboard at:
# https://app.supabase.com/project/[your-project-id]/editor
```

### System Maintenance

**Update scanner code:**
```bash
cd ~/flooorgang
git pull origin main

# Restart venv and reinstall if requirements changed
source venv/bin/activate
pip install -r requirements.txt
```

**System updates (monthly):**
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

**Check disk space:**
```bash
df -h
# Make sure you have at least 1GB free
```

**Check memory usage:**
```bash
free -h
```

### Troubleshooting

**Scanner not running?**
```bash
# Check cron is enabled
sudo systemctl status cron

# Check cron logs for errors
grep CRON /var/log/syslog | tail -20

# Test manual run
~/flooorgang/run_scanner.sh
```

**NBA API timing out?**
```bash
# Check internet connectivity
ping -c 4 google.com
ping -c 4 stats.nba.com

# Check DNS resolution
nslookup stats.nba.com
```

**Graphics not generating?**
```bash
# Check matplotlib dependencies
pip install --upgrade matplotlib pillow

# Check fonts are installed
fc-list | grep -i roboto
```

**Out of disk space?**
```bash
# Check disk usage
df -h

# Clean up old logs (keep last 7 days)
find ~/flooorgang/logs -name "scanner_*.log" -mtime +7 -delete

# Clean up old graphics (keep last 30 days)
find ~/flooorgang/graphics -name "*.png" -mtime +30 -delete

# Clean up pip cache
pip cache purge

# Clean up apt cache
sudo apt clean
```

## Part 5: Optional Enhancements

### Email Notifications on Failure

Install mail utilities:
```bash
sudo apt install -y msmtp msmtp-mta mailutils

# Configure msmtp (example with Gmail)
nano ~/.msmtprc
```

Add configuration:
```
defaults
auth on
tls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile ~/.msmtp.log

account gmail
host smtp.gmail.com
port 587
from your-email@gmail.com
user your-email@gmail.com
password your-app-password

account default : gmail
```

Update run_scanner.sh to send email on failure:
```bash
# Add after EXIT_CODE capture
if [ $EXIT_CODE -ne 0 ]; then
    echo "Scanner failed with exit code $EXIT_CODE" | \
        mail -s "FlooorGang Scanner Failed" your-email@gmail.com
fi
```

### Remote Access with Tailscale (Recommended)

Access your Pi from anywhere without port forwarding:

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Get your Pi's Tailscale IP
tailscale ip -4
```

Now you can SSH from anywhere:
```bash
ssh pi@[tailscale-ip]
```

### Temperature Monitoring

```bash
# Check CPU temperature
vcgencmd measure_temp

# Add to cron to log temperature (optional)
# Add to crontab: */30 * * * * vcgencmd measure_temp >> ~/flooorgang/logs/temp.log
```

## Quick Reference

### Common Commands

```bash
# SSH into Pi
ssh pi@flooorgang-pi.local

# View today's scanner log
tail -f ~/flooorgang/logs/scanner_$(date +%Y%m%d)*.log

# Run scanner manually
cd ~/flooorgang && source venv/bin/activate && python src/scanner_v2.py

# Check cron jobs
crontab -l

# Update code
cd ~/flooorgang && git pull

# Reboot Pi
sudo reboot

# Shutdown Pi
sudo shutdown -h now
```

### Scheduled Times

- **Daily scanner run**: 12:00 PM ET
- **Log retention**: 30 days
- **Graphics retention**: Keep all (or configure in cron)

## Cost Analysis

- **Raspberry Pi 4 (4GB)**: $55 one-time
- **MicroSD card (32GB)**: $10 one-time
- **Power supply**: $8 one-time
- **Case**: $10 one-time
- **Monthly electricity**: ~$0.50/month (3W × 24h × 30d × $0.12/kWh)

**Total startup cost**: ~$83
**Monthly cost**: ~$0.50 (vs $6-40 for cloud hosting)
**Break-even**: 1-2 months

## Next Steps

1. Unbox your Raspberry Pi
2. Follow Part 1 to set up the OS
3. Follow Part 2 to install FlooorGang
4. Follow Part 3 to set up automation
5. Monitor for a few days to ensure stability
6. Add optional enhancements (email notifications, Tailscale)

## Support

If you run into issues:
1. Check the logs: `~/flooorgang/logs/`
2. Test manual execution: `~/flooorgang/run_scanner.sh`
3. Verify cron is running: `sudo systemctl status cron`
4. Check system resources: `free -h && df -h`

Happy scanning!
