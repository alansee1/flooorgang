#!/bin/bash
# Setup cron job for NBA 90%ers scheduler

# Get absolute path to project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🏀 NBA 90%ers - Cron Setup"
echo "=========================="
echo "Project directory: $PROJECT_DIR"
echo ""

# Create cron entries (9 AM ET = 14:00 UTC, adjust for your timezone)
CRON_FETCH="0 14 * * * cd $PROJECT_DIR && /usr/bin/python3 scheduler.py --fetch-schedule >> logs/scheduler.log 2>&1"
CRON_CHECK="*/30 * * * * cd $PROJECT_DIR && /usr/bin/python3 scheduler.py >> logs/scheduler.log 2>&1"

echo "This will add two cron jobs:"
echo ""
echo "1. Fetch schedule at 9 AM ET daily:"
echo "   $CRON_FETCH"
echo ""
echo "2. Check every 30 minutes if it's time to run:"
echo "   $CRON_CHECK"
echo ""
echo "How it works:"
echo "  - 9 AM: Fetch NBA schedule, calculate run time (3hrs before first game)"
echo "  - Every 30 min: Check if it's time, run scanner if yes"
echo "  - Only runs scanner once per day"
echo "  - Gets latest odds right before games start"
echo ""

read -p "Add this cron job? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "scheduler.py"; then
    echo "⚠️  Cron jobs already exist. Updating..."
    # Remove old entries
    crontab -l 2>/dev/null | grep -v "scheduler.py" | crontab -
fi

# Add new entries
(crontab -l 2>/dev/null; echo "$CRON_FETCH"; echo "$CRON_CHECK") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "To verify, run: crontab -l"
echo "To view logs, run: tail -f $PROJECT_DIR/logs/scheduler.log"
echo ""
echo "To remove the cron job later:"
echo "  crontab -l | grep -v 'scheduler.py' | crontab -"
