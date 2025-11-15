#!/bin/bash
# Scanner wrapper for scheduled execution
# Runs scanner with graphics generation and error notifications

# Change to project directory
cd ~/Projects/flooorgang

# Activate virtual environment
source venv/bin/activate

# Run scanner with error handling
echo "Starting scanner at $(date)"

if python3 src/scanner_v2.py --create-graphic; then
    echo "Scanner completed successfully at $(date)"
else
    EXIT_CODE=$?
    echo "Scanner failed at $(date) with exit code $EXIT_CODE"

    # Send error notification to Slack
    python3 -c "
import sys
sys.path.append('src')
from notifier import notify_scanner_error
notify_scanner_error('Scanner exited with code $EXIT_CODE')
" || true  # Don't fail if notification fails

    deactivate
    exit $EXIT_CODE
fi

# Deactivate venv
deactivate
