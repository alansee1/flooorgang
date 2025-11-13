# FlooorGang - Automation Setup

## Overview

The scanner now runs automatically 3 hours before the first game of each day!

## How It Works

1. **Scheduler** (`scheduler.py`) runs every hour via cron
2. Checks if scanner has already run today
3. Fetches today's NBA game schedule
4. Calculates 3 hours before first game
5. If current time >= target time AND hasn't run yet → Runs scanner
6. Scanner generates report + graphic automatically

## Setup Instructions

### 1. Test the Scheduler Logic

Before setting up automation, test that it works:

```bash
python3 test_scheduler.py
```

This shows:
- If scanner already ran today
- First game time
- Target run time (3 hours before)
- Whether it would run now

### 2. Install Cron Job

Run the setup script:

```bash
./setup_cron.sh
```

This adds a cron job that runs the scheduler every hour.

### 3. Verify Cron Job

Check that it was added:

```bash
crontab -l
```

You should see:
```
0 * * * * cd /Users/alansee/Projects/flooorgang && /usr/bin/python3 scheduler.py >> logs/scheduler.log 2>&1
```

### 4. Monitor Logs

Watch the scheduler in action:

```bash
tail -f logs/scheduler.log
```

## Usage Modes

### Manual Mode (Development/Testing)

Use cached data for fast iteration:

```bash
python3 scanner.py
```

- Prompts to use cached odds
- Uses cached player stats
- Fast for testing graphics/logic changes

### Fresh Mode (Production)

Force fresh data from APIs:

```bash
python3 scanner.py --fresh
```

- Skips all caches
- Fetches latest odds and stats
- Used by automated runs

### Automated Mode (Cron)

Runs automatically via cron:
- Checks every hour
- Runs 3 hours before first game
- Only runs once per day
- Uses `--fresh` flag for latest data

## Files

- `scheduler.py` - Main scheduler logic
- `setup_cron.sh` - Cron installation script
- `test_scheduler.py` - Test scheduler without running scanner
- `cache/scanner_lock.json` - Tracks if scanner ran today
- `logs/scheduler.log` - Scheduler activity log

## Troubleshooting

### Scheduler not running?

Check cron job exists:
```bash
crontab -l
```

Check logs for errors:
```bash
cat logs/scheduler.log
```

### Force a fresh run

Delete the lock file:
```bash
rm cache/scanner_lock.json
python3 scheduler.py
```

### Remove automation

Remove cron job:
```bash
crontab -l | grep -v 'scheduler.py' | crontab -
```

## Example Timeline

**Day with 7:00 PM ET first game:**

- 9:00 AM: Scheduler checks → Too early, waits
- 10:00 AM: Scheduler checks → Too early, waits
- 3:00 PM: Scheduler checks → Too early, waits
- 4:00 PM: **Scheduler runs scanner!** (3 hours before 7 PM)
  - Fetches fresh odds
  - Analyzes all players
  - Generates graphic
  - Saves to `graphics/90ers_picks_YYYYMMDD.png`
- 5:00 PM: Scheduler checks → Already ran today, skips
- 6:00 PM: Scheduler checks → Already ran today, skips
- ...continues skipping until next day

**Day with no games:**

- Scheduler checks every hour
- Sees no games scheduled
- Logs "No games today"
- Does nothing

## API Usage

Each automated run uses:
- 1 API call to get game schedule (scheduler check)
- ~10 API calls to get odds (1 per game)
- 0 API calls for NBA stats (free API)

With ~10 games per day × 1 run per day = ~11 calls/day = ~330 calls/month

Well within the 500/month free tier!
