# Scheduler Setup Guide

This guide explains how to set up automated daily execution of the FlooorGang scanner and results tracker on Raspberry Pi.

## How It Works

**Two-stage intelligent scheduling:**

1. **Daily Scheduler (8 AM PST)** - Runs every morning
   - Fetches today's NBA games from The Odds API
   - Finds the earliest game time
   - Schedules scanner to run 3 hours before first game
   - If game is < 3 hours away, runs scanner immediately
   - If no games today, skips scanner entirely

2. **Scanner (Dynamic time)** - Runs at scheduled time
   - Generates picks using scanner_v2.py
   - Creates graphics
   - Saves to database

3. **Results Tracker (9 AM PST next day)** - Scores yesterday's picks
   - Fetches actual NBA stats from yesterday
   - Updates database with results (hit/miss)
   - Only scores unscored picks (safe to re-run)

## Installation on Raspberry Pi

### Step 1: Verify Scripts

Make sure you have the latest code:

```bash
cd ~/Projects/flooorgang
git pull
```

Verify scripts exist:
```bash
ls -lh scripts/schedule_scanner.py
ls -lh scripts/run_scanner.sh
ls -lh scripts/run_results_tracker.sh
```

All should show executable permissions (`-rwxr-xr-x`).

### Step 2: Install `at` Command

The scheduler uses the `at` command to schedule one-time jobs:

```bash
sudo apt-get update
sudo apt-get install -y at
sudo systemctl enable atd
sudo systemctl start atd
```

Verify it's running:
```bash
systemctl status atd
```

### Step 3: Create Logs Directory

```bash
cd ~/Projects/flooorgang
mkdir -p logs
```

### Step 4: Install Crontab

```bash
crontab scripts/crontab.txt
```

Verify it's installed:
```bash
crontab -l
```

You should see:
```
# Daily scheduler - Runs at 8 AM PST (16:00 UTC)
0 16 * * * cd ~/Projects/flooorgang && venv/bin/python3 scripts/schedule_scanner.py >> logs/scheduler.log 2>&1

# Results tracker - Runs at 9 AM PST next day (17:00 UTC)
0 17 * * * cd ~/Projects/flooorgang && bash scripts/run_results_tracker.sh >> logs/results.log 2>&1
```

## Manual Testing

### Test Scheduler (finds games and schedules scanner)

```bash
cd ~/Projects/flooorgang
source venv/bin/activate
python3 scripts/schedule_scanner.py
```

Expected output:
```
======================================================================
FLOOORGANG SCHEDULER - 2025-11-14 08:00 AM PST
======================================================================
First game: Lakers vs Celtics
Game time: 04:00 PM PST
Scanner should run at: 01:00 PM PST
✅ Scanner scheduled for 13:00 PST
```

### Test Scanner Directly

```bash
cd ~/Projects/flooorgang
bash scripts/run_scanner.sh
```

### Test Results Tracker

```bash
cd ~/Projects/flooorgang
bash scripts/run_results_tracker.sh
```

Or score a specific date:
```bash
source venv/bin/activate
python3 scripts/results_tracking/score_picks.py 2025-11-14 --unscored-only
```

## Monitoring

### Check Scheduled Jobs

See upcoming `at` jobs:
```bash
atq
```

View details of job #1:
```bash
at -c 1
```

Remove job #1:
```bash
atrm 1
```

### Check Logs

Scheduler log:
```bash
tail -f ~/Projects/flooorgang/logs/scheduler.log
```

Results tracker log:
```bash
tail -f ~/Projects/flooorgang/logs/results.log
```

Scanner output (from `at` job):
```bash
# at jobs send output via mail, check:
mail
```

## Troubleshooting

### Scheduler runs but scanner doesn't execute

1. Check if `at` job was created:
   ```bash
   atq
   ```

2. Check mail for errors:
   ```bash
   mail
   ```

3. Test script manually:
   ```bash
   bash scripts/run_scanner.sh
   ```

### Results tracker finds no games

NBA API might not have updated yet. Wait a few hours and re-run:
```bash
source venv/bin/activate
python3 scripts/results_tracking/score_picks.py 2025-11-14 --unscored-only
```

### Cron jobs not running

1. Check crontab is installed:
   ```bash
   crontab -l
   ```

2. Check cron service is running:
   ```bash
   systemctl status cron
   ```

3. Check system time and timezone:
   ```bash
   date
   timedatectl
   ```

## Timezone Notes

- **Pi runs in UTC** by default
- **Cron times are in UTC** (16:00 UTC = 8 AM PST)
- **Scheduler script converts to PST** for display
- **NBA API times are in UTC** but we convert to local time

PST to UTC conversion:
- 8 AM PST = 16:00 UTC (scheduler)
- 9 AM PST = 17:00 UTC (results tracker)

## What Happens Each Day

**Morning (8 AM PST):**
1. Scheduler runs via cron
2. Checks The Odds API for today's games
3. If games found, schedules scanner for 3 hours before first game
4. If no games, does nothing

**Afternoon (varies based on games):**
1. Scanner runs at scheduled time
2. Generates picks and graphics
3. Saves to database
4. Graphic saved to `graphics/flooorgang_picks_YYYYMMDD.png`

**Next Morning (9 AM PST):**
1. Results tracker runs via cron
2. Fetches yesterday's date
3. Queries database for yesterday's picks
4. Fetches actual NBA stats for each pick
5. Updates database with results (hit/miss)
6. Only processes unscored picks

## Updating the Code

When you update the code:

```bash
cd ~/Projects/flooorgang
git pull
```

Cron will automatically use the updated scripts on the next run. No need to reinstall crontab.

## Disabling Automation

To stop automated runs:

```bash
crontab -r  # Remove all cron jobs
```

To temporarily disable:
```bash
crontab -e  # Edit crontab
# Add # at start of lines to comment them out
```

## Next Steps

- Add Discord/Slack webhook for daily reports (#79)
- Add error notifications if scanner fails (#78)
- Add Twitter automation to post picks (#108)
