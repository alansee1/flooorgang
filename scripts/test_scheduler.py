"""
Test the scheduler logic without actually running the scanner
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scheduler import get_first_game_time, should_run_scanner, has_run_today
from datetime import datetime, timedelta


def main():
    print("\n🧪 Testing Scheduler Logic")
    print("="*60)

    # Test 1: Check if already ran today
    print("\n1. Checking if scanner already ran today...")
    already_ran = has_run_today()
    print(f"   Result: {'Yes' if already_ran else 'No'}")

    # Test 2: Get first game time
    print("\n2. Fetching first game time...")
    first_game = get_first_game_time()

    if first_game:
        print(f"   First game: {first_game.strftime('%I:%M %p %Z on %Y-%m-%d')}")

        # Calculate target time (3 hours before)
        target_time = first_game - timedelta(hours=3)
        print(f"   Target run time: {target_time.strftime('%I:%M %p %Z')}")

        # Show current time
        now = datetime.now(first_game.tzinfo)
        print(f"   Current time: {now.strftime('%I:%M %p %Z')}")

        # Time difference
        if now < target_time:
            time_until = target_time - now
            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)
            print(f"   Time until target: {hours}h {minutes}m")
        else:
            time_since = now - target_time
            hours = int(time_since.total_seconds() // 3600)
            minutes = int((time_since.total_seconds() % 3600) // 60)
            print(f"   Time since target: {hours}h {minutes}m ago")
    else:
        print("   No games found or error occurred")

    # Test 3: Decision
    print("\n3. Should we run the scanner?")
    should_run = should_run_scanner()
    print(f"   Decision: {'YES - Run scanner!' if should_run else 'NO - Not yet'}")

    print("\n" + "="*60)
    print("Test complete!")


if __name__ == "__main__":
    main()
