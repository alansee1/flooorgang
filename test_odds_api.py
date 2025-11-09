"""
Test The Odds API to see player props data
Run this AFTER you get your API key from https://the-odds-api.com/
"""

import requests
import json
import os
from datetime import datetime

# API Configuration
API_KEY = os.getenv('ODDS_API_KEY', 'YOUR_API_KEY_HERE')
BASE_URL = 'https://api.the-odds-api.com/v4'

def test_sports_list():
    """Test 1: Get list of available sports"""
    print("\n" + "="*60)
    print("TEST 1: Getting list of sports")
    print("="*60)

    url = f"{BASE_URL}/sports"
    params = {'apiKey': API_KEY}

    response = requests.get(url, params=params)

    print(f"Status Code: {response.status_code}")
    print(f"Requests Remaining: {response.headers.get('x-requests-remaining', 'Unknown')}")

    if response.status_code == 200:
        sports = response.json()
        nba_sports = [s for s in sports if 'basketball' in s.get('group', '').lower() or 'nba' in s.get('key', '').lower()]

        print(f"\nFound {len(nba_sports)} NBA/Basketball sport(s):")
        for sport in nba_sports:
            print(f"  - {sport.get('key')}: {sport.get('title')}")

        return nba_sports
    else:
        print(f"Error: {response.text}")
        return None


def test_nba_odds(sport_key='basketball_nba'):
    """Test 2: Get NBA odds/games"""
    print("\n" + "="*60)
    print(f"TEST 2: Getting NBA games for {sport_key}")
    print("="*60)

    url = f"{BASE_URL}/sports/{sport_key}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',  # US bookmakers
        'markets': 'h2h',  # Just checking if games exist first
    }

    response = requests.get(url, params=params)

    print(f"Status Code: {response.status_code}")
    print(f"Requests Remaining: {response.headers.get('x-requests-remaining', 'Unknown')}")

    if response.status_code == 200:
        games = response.json()
        print(f"\nFound {len(games)} upcoming game(s):")

        for i, game in enumerate(games[:5], 1):  # Show first 5
            commence_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
            print(f"\n  Game {i}:")
            print(f"    {game['home_team']} vs {game['away_team']}")
            print(f"    Start: {commence_time.strftime('%Y-%m-%d %H:%M')}")

        return games
    else:
        print(f"Error: {response.text}")
        return None


def test_player_props(games):
    """Test 3: Get NBA player props for a specific game"""
    print("\n" + "="*60)
    print(f"TEST 3: Getting NBA Player Props (using /events endpoint)")
    print("="*60)

    if not games:
        print("\n⚠️  No games available to fetch props for")
        return None

    # Get first game's event ID
    first_game = games[0]
    event_id = first_game.get('id')

    print(f"\nTesting with game:")
    print(f"  {first_game['home_team']} vs {first_game['away_team']}")
    print(f"  Event ID: {event_id}")

    # Use the /events/{eventId}/odds endpoint for player props
    url = f"{BASE_URL}/sports/basketball_nba/events/{event_id}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'player_points,player_rebounds,player_assists,player_threes',
        'oddsFormat': 'american',
    }

    response = requests.get(url, params=params)

    print(f"\nStatus Code: {response.status_code}")
    print(f"Requests Remaining: {response.headers.get('x-requests-remaining', 'Unknown')}")

    if response.status_code == 200:
        event_data = response.json()

        print(f"\n🏀 Player Props Retrieved!")
        print(f"   {event_data.get('home_team', 'Unknown')} vs {event_data.get('away_team', 'Unknown')}")

        if 'bookmakers' in event_data and event_data['bookmakers']:
            bookmaker = event_data['bookmakers'][0]
            print(f"\n   Bookmaker: {bookmaker.get('title', 'Unknown')}")

            if 'markets' in bookmaker and bookmaker['markets']:
                for market in bookmaker['markets']:
                    market_key = market.get('key', 'Unknown')
                    print(f"\n   📊 Market: {market_key}")

                    # Show first few player props
                    if 'outcomes' in market:
                        print(f"      Sample props (first 5):")
                        for outcome in market['outcomes'][:5]:
                            player_name = outcome.get('description', 'Unknown')
                            line = outcome.get('point', 'N/A')
                            price = outcome.get('price', 'N/A')
                            name = outcome.get('name', 'Unknown')
                            print(f"        {name}: {player_name} - Line: {line} (Odds: {price})")
            else:
                print("\n   ⚠️  No markets found in bookmaker data")
        else:
            print("\n   ⚠️  No bookmakers found with player props")

        # Save full response for inspection
        with open('odds_api_sample_response.json', 'w') as f:
            json.dump(event_data, f, indent=2)
        print(f"\n💾 Full response saved to: odds_api_sample_response.json")

        return event_data
    else:
        print(f"\n❌ Error: {response.text}")
        print("\nPossible reasons:")
        print("  1. Player props not available for this game yet")
        print("  2. API key doesn't have access to player props")
        print("  3. Game is too far in the future")
        return None


def main():
    """Run all tests"""
    print("\n🏀 Testing The Odds API for NBA Player Props")
    print("="*60)

    if API_KEY == 'YOUR_API_KEY_HERE':
        print("\n❌ ERROR: Please set your API key first!")
        print("\nOptions:")
        print("1. Set environment variable: export ODDS_API_KEY='your_key'")
        print("2. Edit this file and replace YOUR_API_KEY_HERE with your key")
        print("\nGet your key from: https://the-odds-api.com/")
        return

    print(f"Using API Key: {API_KEY[:10]}...")

    # Test 1: List sports
    sports = test_sports_list()

    if not sports:
        print("\n❌ Could not retrieve sports list. Check your API key.")
        return

    # Test 2: Get NBA games
    games = test_nba_odds()

    # Test 3: Get player props (pass the games list)
    props = test_player_props(games)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\n✅ Tests complete! Check the output above to see:")
    print("  1. If player props are available")
    print("  2. What markets are supported (points, rebounds, assists, etc.)")
    print("  3. How the data is structured")
    print("\nNext step: Build odds_fetcher.py to parse this data")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
