# AWS Lambda Deployment - Summary

## What Was Built

Your FlooorGang scanner is now ready to deploy to AWS Lambda with automated daily scheduling.

### Files Created

1. **`lambda_handler.py`** - Lambda entry point that wraps your scanner_v2.py
2. **`template.yaml`** - AWS SAM template (infrastructure as code)
3. **`samconfig.toml`** - SAM deployment configuration
4. **`deploy.sh`** - One-command deployment script
5. **`requirements-lambda.txt`** - Lambda-optimized dependencies
6. **`test_lambda_local.py`** - Local testing script (no AWS required)
7. **`DEPLOYMENT.md`** - Comprehensive deployment guide
8. **`AWS_QUICKSTART.md`** - Quick start guide (5 steps to deploy)
9. **`.gitignore`** - Updated to exclude AWS build artifacts

### Architecture

```
EventBridge (CloudWatch Events)
  Schedule: Daily at 12 PM EST (5 PM UTC)
    ↓
AWS Lambda Function
  - Runtime: Python 3.11
  - Memory: 512 MB
  - Timeout: 15 minutes
  - Executes: scanner_v2.py
    ↓
External APIs
  - The Odds API (fetch betting lines)
  - NBA API (fetch player stats)
    ↓
Supabase Database
  - Saves scanner runs
  - Saves picks with game history
    ↓
Generated Output
  - PNG graphic (saved to /tmp in Lambda)
  - Twitter post (optional)
```

## Local Testing Results

✅ **Tested successfully on your machine**

```
Scanner found: 12 picks
API requests remaining: 19,423/20,000
Database: Saved as run #3
Graphic: Generated successfully
Status: Lambda handler executed successfully (200 OK)
```

The Lambda handler works perfectly and is ready to deploy.

## Next Steps

### Option 1: Deploy Now

If you have time to set up AWS:

1. **Install prerequisites** (~10 min)
   ```bash
   brew install awscli aws-sam-cli
   ```

2. **Configure AWS** (~5 min)
   ```bash
   aws configure
   # Enter your AWS credentials
   ```

3. **Deploy** (~5 min)
   ```bash
   ./deploy.sh
   ```

4. **Test** (~1 min)
   ```bash
   sam remote invoke ScannerFunction --stack-name flooorgang-scanner
   ```

**Total time: ~20 minutes**

### Option 2: Deploy Later

Everything is ready to go. When you're ready:

1. Read `AWS_QUICKSTART.md` (5-step guide)
2. Run `./deploy.sh`
3. Done!

## What Happens After Deployment

Once deployed, your scanner will:

✅ Run automatically every day at 12 PM EST (5 PM UTC)
✅ Fetch live odds from The Odds API
✅ Analyze player stats from NBA API
✅ Find high-value betting opportunities
✅ Save picks to Supabase database
✅ Generate graphics with game history
✅ Log everything to CloudWatch
✅ Cost: $0/month (within Lambda free tier)

## Current Schedule

**Default:** Daily at 12 PM EST (5 PM UTC)

This timing allows:
- Morning games have completed (11 AM ET tip-offs)
- Evening games haven't started yet (typical 7-8 PM ET)
- Fresh odds are posted by bookmakers
- Scanner runs 3-6 hours before evening games

To change the schedule, edit `template.yaml`:

```yaml
ScheduleExpression:
  Default: "cron(0 17 * * ? *)"  # Current: 12 PM EST
```

## Cost Breakdown

### Lambda (Free Tier)
- **Requests:** 30/month (vs 1M free)
- **Compute:** ~150 GB-seconds/month (vs 400,000 free)
- **Cost:** $0

### Data Transfer
- **The Odds API:** ~350 credits/run × 30 runs = 10,500 credits/month (vs 20,000 plan)
- **Supabase:** Minimal usage (<1 MB/day)
- **CloudWatch Logs:** ~10 MB/month (well within free tier)
- **Cost:** $0

**Total: $0/month** (excluding existing $30 Odds API subscription)

## Features

### What's Included

✅ Lambda function with scanner_v2.py
✅ EventBridge daily schedule
✅ Environment variables (API keys, Supabase)
✅ CloudWatch logging
✅ IAM role with proper permissions
✅ SAM template (infrastructure as code)
✅ One-command deployment script
✅ Local testing capability

### What's Optional (Not Yet Implemented)

⏳ S3 bucket for storing graphics (currently uses /tmp)
⏳ SNS notifications for errors
⏳ CloudWatch alarms for failures
⏳ Lambda Layer for shared dependencies
⏳ Twitter posting integration

These can be added later as needed.

## Monitoring

Once deployed, you can monitor via:

**CloudWatch Logs:**
```bash
sam logs --tail --stack-name flooorgang-scanner
```

**Manual invocation:**
```bash
sam remote invoke ScannerFunction --stack-name flooorgang-scanner
```

**AWS Console:**
- Lambda: https://console.aws.amazon.com/lambda/
- CloudWatch: https://console.aws.amazon.com/cloudwatch/
- EventBridge: https://console.aws.amazon.com/events/

## Troubleshooting

### If deployment fails

**"AWS CLI not found"**
```bash
brew install awscli
aws configure
```

**"SAM CLI not found"**
```bash
brew install aws-sam-cli
```

**"Docker not running"**
```bash
# Start Docker Desktop
open -a Docker
```

**"Access Denied"**
```bash
# Verify credentials
aws sts get-caller-identity
```

### If Lambda fails

**View logs:**
```bash
sam logs --stack-name flooorgang-scanner
```

**Common issues:**
- No NBA games scheduled (off-season)
- API quota exceeded (check The Odds API dashboard)
- Supabase credentials invalid (check environment variables)

## Testing Without Deploying

You can continue testing locally:

```bash
python3 test_lambda_local.py
```

This runs the full scanner without requiring AWS.

## Documentation

- **Quick Start:** `AWS_QUICKSTART.md` (5 steps)
- **Full Guide:** `DEPLOYMENT.md` (comprehensive)
- **This Summary:** `LAMBDA_SUMMARY.md`

## Support

Need help? Check:
- AWS SAM docs: https://docs.aws.amazon.com/serverless-application-model/
- Lambda docs: https://docs.aws.amazon.com/lambda/
- Local testing: Run `python3 test_lambda_local.py`

---

## Summary

✅ **Lambda deployment is ready**
✅ **Tested locally and working**
✅ **One command to deploy: `./deploy.sh`**
✅ **Cost: $0/month**
✅ **Schedule: Daily at 12 PM EST**

When you're ready, follow `AWS_QUICKSTART.md` to deploy in ~20 minutes.
