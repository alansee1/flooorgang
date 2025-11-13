# AWS Lambda Quick Start

Get FlooorGang running on AWS Lambda in 5 steps.

## TL;DR

```bash
# 1. Install prerequisites
brew install awscli aws-sam-cli

# 2. Configure AWS
aws configure

# 3. Deploy
./deploy.sh

# 4. Test
sam remote invoke ScannerFunction --stack-name flooorgang-scanner

# 5. Monitor
sam logs --tail --stack-name flooorgang-scanner
```

## Step-by-Step

### 1. Install AWS CLI and SAM CLI

```bash
# Install both tools
brew install awscli aws-sam-cli

# Verify installation
aws --version  # Should show aws-cli/2.x.x
sam --version  # Should show SAM CLI, version 1.x.x
```

### 2. Configure AWS Credentials

You need an AWS account and IAM credentials.

**Option A: If you already have an AWS account**
```bash
aws configure
```

Enter your:
- AWS Access Key ID: (from IAM user)
- AWS Secret Access Key: (from IAM user)
- Default region: `us-east-1`
- Default output format: `json`

**Option B: If you need to create an AWS account**

1. Go to https://aws.amazon.com/
2. Click "Create an AWS Account"
3. Complete signup (requires credit card, but Lambda has generous free tier)
4. Go to IAM Console → Users → Create User
5. Attach policy: `AdministratorAccess` (for initial setup)
6. Create access key → Save credentials
7. Run `aws configure` with those credentials

### 3. Deploy to Lambda

```bash
./deploy.sh
```

This will:
- Build Lambda deployment package (~2 min)
- Upload to S3
- Create CloudFormation stack with Lambda + EventBridge
- Configure environment variables
- Set up daily schedule

**First time:** SAM will ask you to confirm creating resources. Type `y`.

Expected output:
```
Successfully created/updated stack - flooorgang-scanner in us-east-1
```

### 4. Test the Function

Manually invoke the Lambda function:

```bash
sam remote invoke ScannerFunction --stack-name flooorgang-scanner
```

Or via AWS CLI:

```bash
aws lambda invoke \
    --function-name flooorgang-scanner \
    response.json && cat response.json
```

Expected response:
```json
{
    "statusCode": 200,
    "body": "{\"message\": \"Scanner completed successfully\", \"picks_count\": 8, ...}"
}
```

### 5. View Logs

Watch the logs in real-time:

```bash
sam logs --tail --stack-name flooorgang-scanner
```

Or view recent logs:

```bash
sam logs --stack-name flooorgang-scanner --start-time '5min ago'
```

## Current Schedule

The scanner runs automatically:
- **Time:** 5:00 PM UTC = 12:00 PM EST daily
- **Trigger:** EventBridge (CloudWatch Events)

To change the schedule, edit `template.yaml`:

```yaml
ScheduleExpression:
  Default: "cron(0 17 * * ? *)"
```

Common schedules:
- `cron(0 14 * * ? *)` = 9 AM EST
- `cron(0 16 * * ? *)` = 11 AM EST
- `cron(0 17 * * ? *)` = 12 PM EST (current)
- `cron(0 18 * * ? *)` = 1 PM EST

After editing, redeploy:
```bash
./deploy.sh
```

## Costs

**Expected monthly cost: $0**

Lambda free tier includes:
- 1M requests/month (you'll use ~30)
- 400,000 GB-seconds (you'll use ~150)

You'll stay well within the free tier running once per day.

## Troubleshooting

**"Docker is not running"**
```bash
# Start Docker Desktop, then retry
open -a Docker
./deploy.sh
```

**"Access Denied" errors**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Should show your account ID and user ARN
# If not, reconfigure:
aws configure
```

**Lambda times out**
- Default timeout is 15 minutes (900 seconds)
- Scanner usually completes in 2-5 minutes
- Check CloudWatch logs for errors

**No picks found**
- Scanner needs NBA games scheduled for today
- Check if it's NBA season
- View logs: `sam logs --tail --stack-name flooorgang-scanner`

## What's Next?

Once deployed, your scanner will:
1. ✅ Run automatically every day at 12 PM EST
2. ✅ Fetch odds from The Odds API
3. ✅ Analyze player stats from NBA API
4. ✅ Save picks to Supabase
5. ✅ Generate graphics (saved in Lambda /tmp)
6. ⏳ Post to Twitter (if configured)

To enable Twitter posting:
- Verify Twitter credentials in `.env`
- Uncomment Twitter posting code in `scanner_v2.py`

## Monitoring

**Check if schedule is active:**
```bash
aws events list-rules | grep flooorgang
```

**Manually trigger:**
```bash
sam remote invoke ScannerFunction --stack-name flooorgang-scanner
```

**View all Lambda functions:**
```bash
aws lambda list-functions
```

**Delete everything:**
```bash
sam delete --stack-name flooorgang-scanner
```

## Support

Questions? Check:
- Full docs: `DEPLOYMENT.md`
- SAM CLI docs: https://docs.aws.amazon.com/serverless-application-model/
- AWS Lambda Console: https://console.aws.amazon.com/lambda/
