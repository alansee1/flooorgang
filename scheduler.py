"""
Dynamic Scheduler for NBA 90%ers Scanner
Uses NBA API to get today's first game, runs 3 hours before
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from nba_api.live.nba.endpoints import scoreboard


CACHE_DIR = 'cache'
LOCK_FILE = os.path.join(CACHE_DIR, 'scanner_lock.json')
SCHEDULE_FILE = os.path.join(CACHE_DIR, 'todays_schedule.json')
LOG_FILE = 'logs/scheduler.log'


def ensure_dirs():
    """Create necessary directories"""
    os.makedirs('cache', exist_ok=True)
    os.makedirs('logs', exist_ok=True)


def log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)

    ensure_dirs()
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')


def fetch_and_save_schedule():
    """
    Fetch today's games from NBA API and save run time
    Called at 9 AM daily
    """
    log("Fetching today's NBA schedule...")

    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()

        if not games:
            log("No games scheduled today")
            # Save empty schedule
            ensure_dirs()
            with open(SCHEDULE_FILE, 'w') as f:
                json.dump({'run_time': None, 'fetched_at': datetime.now().isoformat()}, f)
            return None

        # Parse game times and find earliest
        game_times = []
        for game in games:
            game_time_str = game.get('gameTimeUTC')
            if game_time_str:
                game_time = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
                game_times.append(game_time)

        if not game_times:
            return None

        first_game = min(game_times)
        run_time = first_game - timedelta(hours=3)

        log(f"First game today: {first_game.strftime('%I:%M %p %Z')}")
        log(f"Will run scanner at: {run_time.strftime('%I:%M %p %Z')}")

        # Save schedule
        ensure_dirs()
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump({
                'run_time': run_time.isoformat(),
                'first_game': first_game.isoformat(),
                'fetched_at': datetime.now().isoformat()
            }, f, indent=2)

        return run_time

    except Exception as e:
        log(f"Error fetching today's games: {e}")
        return None


def load_todays_schedule():
    """Load today's saved schedule"""
    if not os.path.exists(SCHEDULE_FILE):
        return None

    try:
        with open(SCHEDULE_FILE, 'r') as f:
            data = json.load(f)

        # Check if schedule is from today
        fetched_at = datetime.fromisoformat(data['fetched_at'])
        if fetched_at.date() != datetime.now().date():
            log("Schedule is from previous day, ignoring")
            return None

        run_time_str = data.get('run_time')
        if not run_time_str:
            return None

        return datetime.fromisoformat(run_time_str)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        log(f"Error loading schedule: {e}")
        return None




def has_run_today():
    """Check if scanner already ran today"""
    if not os.path.exists(LOCK_FILE):
        return False

    try:
        with open(LOCK_FILE, 'r') as f:
            lock_data = json.load(f)

        last_run = datetime.fromisoformat(lock_data['last_run'])
        today = datetime.now().date()

        return last_run.date() == today
    except (json.JSONDecodeError, KeyError, ValueError):
        return False


def mark_as_run():
    """Mark that scanner ran today"""
    ensure_dirs()
    lock_data = {
        'last_run': datetime.now().isoformat()
    }
    with open(LOCK_FILE, 'w') as f:
        json.dump(lock_data, f, indent=2)


def should_run_now():
    """
    Check if we should run scanner now based on saved schedule

    Returns:
        True if it's time to run
    """
    # Already ran today?
    if has_run_today():
        log("Scanner already ran today")
        return False

    # Load today's schedule
    run_time = load_todays_schedule()

    if not run_time:
        log("No schedule found for today (run with --fetch-schedule first)")
        return False

    # Check if we're past the run time
    now = datetime.now(run_time.tzinfo)

    log(f"Scheduled run time: {run_time.strftime('%I:%M %p %Z')}")
    log(f"Current time: {now.strftime('%I:%M %p %Z')}")

    if now >= run_time:
        log(f"✅ Past scheduled time, running scanner!")
        return True
    else:
        time_until = run_time - now
        hours = int(time_until.total_seconds() // 3600)
        minutes = int((time_until.total_seconds() % 3600) // 60)
        log(f"⏰ Not yet. {hours}h {minutes}m until run time")
        return False


def run_scanner():
    """Execute scanner with --fresh flag"""
    log("="*60)
    log("RUNNING SCANNER")
    log("="*60)

    try:
        result = subprocess.run(
            [sys.executable, 'scanner.py', '--fresh'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=600
        )

        log("Scanner output:")
        log(result.stdout)

        if result.stderr:
            log("Scanner errors:")
            log(result.stderr)

        if result.returncode == 0:
            log("✅ Scanner completed successfully")
            mark_as_run()
            return True
        else:
            log(f"❌ Scanner failed with code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        log("❌ Scanner timed out")
        return False
    except Exception as e:
        log(f"❌ Error running scanner: {e}")
        return False


def main():
    """Main scheduler entry point"""

    # Fetch schedule mode (run at 9 AM)
    if '--fetch-schedule' in sys.argv:
        log("\n📅 Fetching today's schedule...")
        fetch_and_save_schedule()
        return

    # Check and run mode (runs every 30 min)
    log("\n🔍 Scheduler check...")

    if should_run_now():
        success = run_scanner()
        if success:
            log("🎉 Daily scan complete!\n")
        else:
            log("⚠️ Scan failed\n")
    else:
        log("Nothing to do\n")


if __name__ == "__main__":
    main()
