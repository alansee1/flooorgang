# Twitter Integration

Auto-posting NBA prop bet picks to [@FlooorGang](https://twitter.com/FlooorGang)

## Setup

1. **Get Twitter API credentials** from https://developer.twitter.com/
   - Create an app in the Developer Portal
   - Get API Key, API Secret, Access Token, and Access Token Secret

2. **Add credentials to `.env`:**
   ```bash
   TWITTER_API_KEY=your_api_key_here
   TWITTER_API_SECRET=your_api_secret_here
   TWITTER_ACCESS_TOKEN=your_access_token_here
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
   ```

3. **Install dependencies:**
   ```bash
   pip3 install tweepy==4.14.0
   ```

## Usage

### Manual Posting

Run the scanner with the `--tweet` flag to automatically post:

```bash
python3 -m src.scanner --tweet
```

This will:
1. Generate today's picks graphic
2. Upload the image to Twitter
3. Post a tweet with the graphic and analytics

### Automated Posting (Cron)

The scheduler automatically posts when it runs (already configured):

```bash
# Scheduler runs daily with --tweet flag
python3 -m src.scheduler
```

Your cron job already handles this:
- Fetches schedule at 9 AM ET
- Runs scanner 3 hours before first game
- Automatically posts to Twitter

### Test Connection

Verify your Twitter API credentials:

```bash
python3 src/twitter_poster.py
```

## Tweet Format

The automated tweets include:
- 🏀 Number of high-confidence picks
- Brief explanation of "floor stats"
- Hashtags: #NBA #PropBets #SportsBetting
- Generated graphic with pick details

## Troubleshooting

**401 Unauthorized:** Check that you're using the correct OAuth 1.0a credentials (API Key/Secret, not Client ID/Secret)

**Media upload fails:** Ensure Access Token has Read and Write permissions

**Rate limits:** Twitter Free tier allows 1,500 tweets/month (50/day) - plenty for daily picks
