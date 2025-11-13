"""
Quick test to see which APIs are reachable from Lambda
"""
import requests
import time

def test_api(name, url, timeout=5):
    """Test if an API is reachable"""
    try:
        start = time.time()
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start

        print(f"✅ {name}: {response.status_code} ({elapsed:.2f}s)")
        return True
    except requests.exceptions.Timeout:
        print(f"⏱️  {name}: TIMEOUT (>{timeout}s)")
        return False
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__} - {e}")
        return False

def main():
    print("Testing API accessibility...\n")

    tests = [
        ("NBA Stats API", "https://stats.nba.com/stats/commonplayerinfo?PlayerID=2544"),
        ("BallDontLie", "https://api.balldontlie.io/v1/players"),
        ("The Odds API", "https://api.the-odds-api.com/v4/sports"),
        ("Google", "https://www.google.com"),
    ]

    results = {}
    for name, url in tests:
        results[name] = test_api(name, url)
        print()

    print("\n" + "="*50)
    print("SUMMARY:")
    print("="*50)
    for name, success in results.items():
        status = "✅ WORKS" if success else "❌ BLOCKED/TIMEOUT"
        print(f"{name}: {status}")

if __name__ == "__main__":
    main()
