#!/bin/bash
# Scanner wrapper for scheduled execution
# Runs scanner with graphics generation

set -e  # Exit on error

# Change to project directory
cd ~/Projects/flooorgang

# Activate virtual environment
source venv/bin/activate

# Run scanner with graphics
echo "Starting scanner at $(date)"
python3 src/scanner_v2.py --create-graphic

# Deactivate venv
deactivate

echo "Scanner completed at $(date)"
