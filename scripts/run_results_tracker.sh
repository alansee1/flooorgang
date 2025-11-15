#!/bin/bash
# Results tracker wrapper for scheduled execution
# Scores yesterday's picks using --unscored-only flag

# Change to project directory
cd ~/Projects/flooorgang

# Activate virtual environment
source venv/bin/activate

# Get yesterday's date in YYYY-MM-DD format
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# Run results tracker with error handling
echo "Starting results tracker at $(date)"
echo "Scoring picks from $YESTERDAY"

if python3 scripts/results_tracking/score_picks.py "$YESTERDAY" --unscored-only; then
    echo "Results tracker completed successfully at $(date)"
else
    EXIT_CODE=$?
    echo "Results tracker failed at $(date) with exit code $EXIT_CODE"

    # Send error notification to Slack
    python3 -c "
import sys
sys.path.append('src')
from notifier import notify_results_tracker_error
notify_results_tracker_error('Results tracker exited with code $EXIT_CODE for date $YESTERDAY')
" || true  # Don't fail if notification fails

    deactivate
    exit $EXIT_CODE
fi

# Deactivate venv
deactivate
