# The Odds API Setup Guide

## Step 1: Sign Up for Free Account

1. Go to: https://the-odds-api.com/
2. Click "Get API Key" button
3. Sign up with your email
4. You'll receive an API key via email

**Free Tier:** 500 credits/month (should be plenty for daily morning scans)

## Step 2: Get Your API Key

1. Visit: https://dash.the-odds-api.com/
2. Log in with your account
3. Copy your API key from the dashboard

## Step 3: Store API Key

Create a `.env` file in this directory:

```bash
# .env
ODDS_API_KEY=your_api_key_here
```

**IMPORTANT:** Add `.env` to `.gitignore` so you don't commit your API key!

## Step 4: Test the API

Once you have your key, run:

```bash
python3 test_odds_api.py
```

## Useful Documentation Links

- **Main Docs:** https://the-odds-api.com/liveapi/guides/v4/
- **Player Props:** https://the-odds-api.com/sports-odds-data/betting-markets.html#player-props-api-markets
- **Code Samples:** https://the-odds-api.com/liveapi/guides/v4/samples.html

## What We Need to Test

1. Can we get NBA player props?
2. What bookmakers have player props available? (DraftKings, FanDuel, etc.)
3. What stats are available? (PTS, REB, AST, etc.)
4. How is the data formatted?
5. How many credits does one request cost?

## Expected Response Format (to verify)

We expect something like:
```json
{
  "player": "Shai Gilgeous-Alexander",
  "market": "player_points",
  "line": 30.5,
  "over_odds": -110,
  "under_odds": -110
}
```
