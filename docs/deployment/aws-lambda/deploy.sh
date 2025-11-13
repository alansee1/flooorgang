#!/bin/bash
set -e

echo "🚀 FlooorGang Lambda Deployment Script"
echo "======================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI not found. Please install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Load environment variables
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

source .env

echo ""
echo "📦 Step 1: Building SAM application..."
sam build --use-container

echo ""
echo "🚀 Step 2: Deploying to AWS..."
sam deploy \
    --no-confirm-changeset \
    --parameter-overrides \
        OddsApiKey="${ODDS_API_KEY}" \
        SupabaseUrl="${SUPABASE_URL}" \
        SupabaseAnonKey="${SUPABASE_ANON_KEY}" \
        SupabaseServiceRoleKey="${SUPABASE_SERVICE_ROLE_KEY}" \
        TwitterApiKey="${TWITTER_API_KEY}" \
        TwitterApiSecret="${TWITTER_API_SECRET}" \
        TwitterAccessToken="${TWITTER_ACCESS_TOKEN}" \
        TwitterAccessTokenSecret="${TWITTER_ACCESS_TOKEN_SECRET}"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   - Test with: sam remote invoke ScannerFunction"
echo "   - View logs: sam logs --tail --stack-name flooorgang-scanner"
echo "   - Update schedule: Edit template.yaml ScheduleExpression parameter"
