#!/usr/bin/env python3
"""
Test the Lambda handler locally without AWS
"""
import json
from datetime import datetime
from lambda_handler import lambda_handler


def test_local():
    """Run the Lambda handler locally"""
    print("=" * 70)
    print("Testing Lambda handler locally (without AWS)")
    print("=" * 70)
    print()

    # Simulate EventBridge event
    test_event = {
        'version': '0',
        'id': 'test-event-id',
        'detail-type': 'Scheduled Event',
        'source': 'aws.events',
        'time': datetime.utcnow().isoformat() + 'Z',
        'region': 'us-east-1',
        'resources': ['arn:aws:events:us-east-1:123456789012:rule/test-rule']
    }

    # Simulate Lambda context (minimal)
    class Context:
        function_name = 'flooorgang-scanner'
        memory_limit_in_mb = 512
        invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:flooorgang-scanner'
        aws_request_id = 'test-request-id'

    context = Context()

    print("Invoking lambda_handler...")
    print()

    try:
        # Invoke the handler
        response = lambda_handler(test_event, context)

        print()
        print("=" * 70)
        print("Lambda Response:")
        print("=" * 70)
        print(json.dumps(response, indent=2))
        print()

        if response['statusCode'] == 200:
            print("✅ Lambda handler executed successfully!")
        else:
            print(f"⚠️  Lambda returned status code {response['statusCode']}")

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Error:")
        print("=" * 70)
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_local()
