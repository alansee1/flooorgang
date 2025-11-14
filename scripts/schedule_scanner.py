#!/usr/bin/env python3
"""
Daily scheduler that finds first game time and schedules scanner 3 hours before.
Runs daily at 8 AM PST via cron.
"""

import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

from odds_fetcher_v2 import OddsFetcher

def get_first_game_time():
    """Get the earliest game time for today"""
    fetcher = OddsFetcher()
    games = fetcher.get_todays_games()

    if not games:
        print("No games found for today")
        return None

    # Find earliest game
    earliest_game = min(games, key=lambda g: g['commence_time'])

    # Parse commence_time (ISO format string)
    game_time = datetime.fromisoformat(earliest_game['commence_time'].replace('Z', '+00:00'))

    # Convert to PST for display
    pst = ZoneInfo("America/Los_Angeles")
    game_time_pst = game_time.astimezone(pst)

    print(f"First game: {earliest_game['home_team']} vs {earliest_game['away_team']}")
    print(f"Game time: {game_time_pst.strftime('%I:%M %p %Z')}")

    return game_time

def schedule_scanner(game_time):
    """Schedule scanner to run 3 hours before game time"""
    now = datetime.now(ZoneInfo("UTC"))
    scanner_time = game_time - timedelta(hours=3)

    time_until_scanner = (scanner_time - now).total_seconds()

    pst = ZoneInfo("America/Los_Angeles")
    scanner_time_pst = scanner_time.astimezone(pst)

    print(f"Scanner should run at: {scanner_time_pst.strftime('%I:%M %p %Z')}")

    # If less than 3 hours until game, run immediately
    if time_until_scanner <= 0:
        print("⚠️  Game is less than 3 hours away! Running scanner immediately...")
        run_scanner_now()
        return

    # If less than 10 minutes until scheduled time, run immediately
    if time_until_scanner < 600:  # 10 minutes
        print("⚠️  Scheduled time is very soon! Running scanner immediately...")
        run_scanner_now()
        return

    # Schedule using 'at' command
    # Format: HH:MM (24-hour format in local time)
    at_time = scanner_time_pst.strftime('%H:%M')

    script_path = os.path.join(os.path.dirname(__file__), 'run_scanner.sh')

    try:
        # Use 'at' to schedule one-time job
        cmd = f'echo "{script_path}" | at {at_time}'
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Scanner scheduled for {at_time} PST")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to schedule scanner: {e}")
        print("Falling back to running immediately...")
        run_scanner_now()

def run_scanner_now():
    """Run scanner immediately"""
    script_path = os.path.join(os.path.dirname(__file__), 'run_scanner.sh')
    try:
        subprocess.run([script_path], check=True)
        print("✅ Scanner completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Scanner failed: {e}")
        sys.exit(1)

def main():
    print("="*70)
    print(f"FLOOORGANG SCHEDULER - {datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %I:%M %p %Z')}")
    print("="*70)

    # Get first game time
    game_time = get_first_game_time()

    if not game_time:
        print("No games today - skipping scanner")
        return

    # Schedule scanner
    schedule_scanner(game_time)

if __name__ == "__main__":
    main()
