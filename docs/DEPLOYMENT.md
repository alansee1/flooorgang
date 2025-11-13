# FlooorGang AWS Lambda Deployment Guide

This guide will help you deploy the FlooorGang scanner to AWS Lambda with automated daily scheduling.

## Architecture

```
EventBridge (Daily Schedule)
    ↓
AWS Lambda Function
    ↓ Fetches odds & stats
The Odds API + NBA API
    ↓ Saves results
Supabase Database
    ↓ Generates graphic
S3 (optional for images)
    ↓ Posts picks
Twitter API
```

## Prerequisites

### 1. AWS Account
- Sign up at https://aws.amazon.com/
- Create an IAM user with appropriate permissions

### 2. AWS CLI
```bash
# Install (macOS)
brew install awscli

# Configure with your credentials
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (`json`)

### 3. SAM CLI
```bash
# Install (macOS)
brew tap aws/tap
brew install aws-sam-cli

# Verify installation
sam --version
```

### 4. Docker
SAM CLI uses Docker to build Lambda packages locally.

```bash
# Install Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Verify Docker is running
docker ps
```

## Deployment Steps

### Step 1: Review Configuration

Check `template.yaml` for the default schedule:
```yaml
ScheduleExpression:
  Default: "cron(0 17 * * ? *)"  # 5 PM UTC = 12 PM EST
```

EventBridge cron format: `cron(minute hour day month day-of-week year)`

**Common schedules:**
- `cron(0 17 * * ? *)` - Daily at 12 PM EST (5 PM UTC)
- `cron(0 16 * * ? *)` - Daily at 11 AM EST (4 PM UTC)
- `cron(0 */6 * * ? *)` - Every 6 hours
- `rate(1 day)` - Once per day (non-specific time)

### Step 2: Build and Deploy

Run the deployment script:

```bash
./deploy.sh
```

This will:
1. Build the Lambda package with all dependencies
2. Create CloudFormation stack with Lambda + EventBridge
3. Upload code to S3 and deploy to Lambda
4. Configure environment variables from `.env`
5. Set up daily schedule

**First deployment:** SAM will prompt you to confirm creating AWS resources. Type `y` to proceed.

### Step 3: Verify Deployment

Check that Lambda function was created:

```bash
aws lambda list-functions --query "Functions[?FunctionName=='flooorgang-scanner']"
```

Check that EventBridge rule was created:

```bash
aws events list-rules --query "Rules[?contains(Name, 'flooorgang')]"
```

### Step 4: Test Manually

Invoke the Lambda function manually to test:

```bash
sam remote invoke ScannerFunction --stack-name flooorgang-scanner
```

Or via AWS CLI:

```bash
aws lambda invoke \
    --function-name flooorgang-scanner \
    --payload '{}' \
    response.json

cat response.json
```

### Step 5: Monitor Logs

View real-time logs:

```bash
sam logs --tail --stack-name flooorgang-scanner
```

Or via AWS CloudWatch:
- Go to AWS Console → CloudWatch → Log Groups
- Find `/aws/lambda/flooorgang-scanner`

## Updating the Deployment

### Update Code

After making code changes, redeploy:

```bash
./deploy.sh
```

SAM will detect changes and only update what's necessary.

### Update Environment Variables

Edit `.env` locally, then redeploy:

```bash
./deploy.sh
```

Or update directly in Lambda console:
- AWS Console → Lambda → flooorgang-scanner → Configuration → Environment variables

### Update Schedule

Edit `template.yaml` → `ScheduleExpression` parameter, then:

```bash
sam deploy
```

## Cost Estimates

Based on daily execution:

**Lambda:**
- Free tier: 1M requests/month, 400,000 GB-seconds compute
- Expected: 1 execution/day × 30 days = 30 requests/month
- Runtime: ~2-5 minutes at 512 MB = ~60-150 GB-seconds/month
- **Cost: $0 (well within free tier)**

**The Odds API:**
- Already paying $30/month for 20,000 credits
- Scanner uses ~350 credits per run
- 30 runs/month = 10,500 credits
- **Cost: Covered by existing plan**

**Supabase:**
- Free tier: 500 MB database, 2 GB bandwidth
- Expected: Minimal usage (<1 MB/day)
- **Cost: $0 (well within free tier)**

**Total monthly cost: ~$0** (excluding existing $30 Odds API subscription)

## Troubleshooting

### Build Errors

**Issue:** "Docker daemon not running"
```bash
# Start Docker Desktop, then retry
sam build --use-container
```

**Issue:** "No module named 'nba_api'"
```bash
# Dependencies should be installed automatically by SAM
# If issues persist, check requirements-lambda.txt
```

### Deployment Errors

**Issue:** "Unable to upload artifact ... Access Denied"
```bash
# Check AWS credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

**Issue:** "Stack with id flooorgang-scanner does not exist"
```bash
# First deployment uses different command
sam deploy --guided
```

### Runtime Errors

**Issue:** Lambda timeout after 3 seconds
- The scanner takes 2-5 minutes to run
- Check `template.yaml` has `Timeout: 900` (15 minutes)

**Issue:** "Unable to import module 'lambda_handler'"
- Check that `lambda_handler.py` is in the root directory
- Check that `src/` folder is included in deployment

**Issue:** "No picks found"
- Check that it's running during NBA season
- Check that games are scheduled for today
- Review CloudWatch logs for API errors

## Manual Invocation

You can also trigger the scanner manually via AWS Console:

1. Go to AWS Lambda → flooorgang-scanner
2. Click "Test" tab
3. Create test event with empty JSON: `{}`
4. Click "Test" button

Results will appear in execution logs.

## Disabling Automated Runs

Temporarily disable the schedule:

```bash
# Disable EventBridge rule
aws events disable-rule --name flooorgang-scanner-DailySchedule-XXXXX

# Re-enable later
aws events enable-rule --name flooorgang-scanner-DailySchedule-XXXXX
```

Or delete the entire stack:

```bash
sam delete --stack-name flooorgang-scanner
```

## Next Steps

- [ ] Set up CloudWatch alarms for Lambda failures
- [ ] Add S3 bucket for storing generated graphics
- [ ] Configure SNS topic for error notifications
- [ ] Add Lambda Layer for shared dependencies (reduce package size)
- [ ] Consider Step Functions for multi-stage workflow (fetch → analyze → post)

## Support

- AWS Lambda docs: https://docs.aws.amazon.com/lambda/
- SAM docs: https://docs.aws.amazon.com/serverless-application-model/
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/
