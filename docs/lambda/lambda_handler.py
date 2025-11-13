"""
AWS Lambda handler for FlooorGang scanner
"""
import os
import sys
import json
from datetime import datetime
import requests
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Uncomment to run actual scanner
# from scanner_v2 import Scanner


def test_api_access():
    """Quick test to see which APIs work from Lambda"""
    tests = [
        ("NBA Stats API", "https://stats.nba.com/stats/commonplayerinfo?PlayerID=2544"),
        ("BallDontLie", "https://api.balldontlie.io/v1/players"),
        ("The Odds API", "https://api.the-odds-api.com/v4/sports"),
    ]

    results = {}
    for name, url in tests:
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            elapsed = time.time() - start
            results[name] = {"status": "✅ SUCCESS", "code": response.status_code, "time": f"{elapsed:.2f}s"}
            print(f"✅ {name}: {response.status_code} ({elapsed:.2f}s)")
        except requests.exceptions.Timeout:
            results[name] = {"status": "❌ TIMEOUT", "time": ">5s"}
            print(f"⏱️  {name}: TIMEOUT")
        except Exception as e:
            results[name] = {"status": "❌ ERROR", "error": str(e)}
            print(f"❌ {name}: {e}")

    return results


def lambda_handler(event, context):
    """
    AWS Lambda entry point

    Args:
        event: EventBridge scheduled event or manual invocation
        context: Lambda context object

    Returns:
        Response with status code and results
    """
    print(f"FlooorGang API Test Lambda started at {datetime.utcnow()}")
    print(f"Event: {json.dumps(event)}")

    try:
        # Test API accessibility
        results = test_api_access()

        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'API test completed',
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }, indent=2)
        }

    except Exception as e:
        print(f"Error running scanner: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Scanner failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


if __name__ == "__main__":
    # For local testing
    test_event = {
        'source': 'local-test',
        'time': datetime.utcnow().isoformat()
    }
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
