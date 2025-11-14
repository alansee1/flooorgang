#!/bin/bash
# Results tracker wrapper for scheduled execution
# Scores yesterday's picks using --unscored-only flag

set -e  # Exit on error

# Change to project directory
cd ~/Projects/flooorgang

# Activate virtual environment
source venv/bin/activate

# Get yesterday's date in YYYY-MM-DD format
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# Run results tracker for yesterday's picks (unscored only)
echo "Starting results tracker at $(date)"
echo "Scoring picks from $YESTERDAY"
python3 scripts/results_tracking/score_picks.py "$YESTERDAY" --unscored-only

# Deactivate venv
deactivate

echo "Results tracker completed at $(date)"
