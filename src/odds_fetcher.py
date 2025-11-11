"""
Odds Fetcher Module
Fetches betting lines from The Odds API for NBA player props
"""

import requests
import os
import time
from datetime import datetime


class OddsFetcher:
    """Fetch and parse betting odds from The Odds API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.sport_key = 'basketball_nba'
        self.requests_remaining = None  # Track remaining API requests
        self.games_scheduled = None  # Track number of games scheduled
        self.games_with_props = None  # Track number of games with actual props

        if not self.api_key:
            raise ValueError("API key required. Set ODDS_API_KEY env var or pass to constructor")

    def get_todays_games(self):
        """
        Get list of today's NBA games
        Returns list of game objects with event IDs
        """
        url = f"{self.base_url}/sports/{self.sport_key}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'h2h',  # Just get game list
        }

        response = requests.get(url, params=params)

        # Track remaining requests
        self.requests_remaining = response.headers.get('x-requests-remaining', 'Unknown')

        if response.status_code != 200:
            raise Exception(f"Error fetching games: {response.text}")

        games = response.json()
        print(f"Found {len(games)} upcoming NBA games")
        print(f"Requests Remaining: {self.requests_remaining}")

        return games

    def get_todays_events(self):
        """
        Get today's events (lightweight, just times and IDs)
        Similar to get_todays_games() but without printing
        Used by scheduler to check game times
        """
        url = f"{self.base_url}/sports/{self.sport_key}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'h2h',
        }

        response = requests.get(url, params=params)
        self.requests_remaining = response.headers.get('x-requests-remaining', 'Unknown')

        if response.status_code != 200:
            raise Exception(f"Error fetching events: {response.text}")

        return response.json()

    def get_player_props_for_game(self, event_id):
        """
        Get player props for a specific game
        Returns dict mapping player names to their prop lines
        """
        url = f"{self.base_url}/sports/{self.sport_key}/events/{event_id}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'player_points,player_rebounds,player_assists,player_threes,player_steals,player_blocks',
            'oddsFormat': 'american',
        }

        response = requests.get(url, params=params)

        # Track remaining requests
        self.requests_remaining = response.headers.get('x-requests-remaining', 'Unknown')

        if response.status_code != 200:
            print(f"Warning: Could not fetch props for event {event_id}: {response.text}")
            return None

        event_data = response.json()
        return self._parse_player_props(event_data)

    def get_team_totals_for_game(self, event_id):
        """
        Get team totals for a specific game
        Returns dict: {home_team: line, away_team: line}
        """
        url = f"{self.base_url}/sports/{self.sport_key}/events/{event_id}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'team_totals',
            'oddsFormat': 'american',
        }

        response = requests.get(url, params=params)

        # Track remaining requests
        self.requests_remaining = response.headers.get('x-requests-remaining', 'Unknown')

        if response.status_code != 200:
            print(f"Warning: Could not fetch team totals for event {event_id}: {response.text}")
            return None

        event_data = response.json()
        return self._parse_team_totals(event_data)

    def _parse_player_props(self, event_data):
        """
        Parse player props from API response
        Returns dict: {player_name: {stat: line}}

        Example:
        {
            "Giannis Antetokounmpo": {
                "PTS": 30.5,
                "REB": 11.5,
                "AST": 6.5
            }
        }
        """
        player_props = {}

        # Market name mapping
        market_map = {
            'player_points': 'PTS',
            'player_rebounds': 'REB',
            'player_assists': 'AST',
            'player_threes': 'FG3M',
            'player_steals': 'STL',
            'player_blocks': 'BLK'
        }

        if 'bookmakers' not in event_data or not event_data['bookmakers']:
            return player_props

        # Use first bookmaker (usually FanDuel)
        bookmaker = event_data['bookmakers'][0]

        if 'markets' not in bookmaker:
            return player_props

        for market in bookmaker['markets']:
            market_key = market.get('key')
            stat_name = market_map.get(market_key)

            if not stat_name:
                continue

            # Process outcomes (each player appears twice: Over and Under)
            for outcome in market.get('outcomes', []):
                # Only process "Over" lines (we don't need both)
                if outcome.get('name') != 'Over':
                    continue

                player_name = outcome.get('description', '').strip()
                line = outcome.get('point')

                if not player_name or line is None:
                    continue

                # Initialize player if not seen yet
                if player_name not in player_props:
                    player_props[player_name] = {}

                # Add this stat's line
                player_props[player_name][stat_name] = line

        return player_props

    def _parse_team_totals(self, event_data):
        """
        Parse team totals from API response
        Returns dict: {team_name: line}

        Example:
        {
            "Los Angeles Lakers": 112.5,
            "Boston Celtics": 108.5
        }
        """
        team_totals = {}

        if 'bookmakers' not in event_data or not event_data['bookmakers']:
            return team_totals

        # Use first bookmaker (usually FanDuel)
        bookmaker = event_data['bookmakers'][0]

        if 'markets' not in bookmaker:
            return team_totals

        for market in bookmaker['markets']:
            if market.get('key') != 'team_totals':
                continue

            # Process outcomes (each team has Over and Under)
            for outcome in market.get('outcomes', []):
                # Only process "Over" lines
                if outcome.get('name') != 'Over':
                    continue

                team_name = outcome.get('description', '').strip()
                line = outcome.get('point')

                if not team_name or line is None:
                    continue

                # Add team total
                team_totals[team_name] = line

        return team_totals

    def get_all_player_props(self, delay=0.2):
        """
        Get player props for all today's games
        Returns dict: {player_name: {stat: line}}

        Args:
            delay: Seconds to wait between API calls (default 0.2s = 5 req/sec for paid tier)
        """
        print("\n" + "="*60)
        print("Fetching Player Props from The Odds API")
        print("="*60)

        # Step 1: Get today's games
        games = self.get_todays_games()

        if not games:
            print("No games found")
            self.games_scheduled = 0
            self.games_with_props = 0
            return {}

        # Track total games scheduled
        self.games_scheduled = len(games)

        # Step 2: Fetch props for each game
        all_props = {}
        games_with_props_count = 0

        for i, game in enumerate(games, 1):
            event_id = game.get('id')
            home_team = game.get('home_team', 'Unknown')
            away_team = game.get('away_team', 'Unknown')

            print(f"\n[{i}/{len(games)}] {away_team} @ {home_team}")

            props = self.get_player_props_for_game(event_id)

            if props:
                games_with_props_count += 1
                print(f"  Found props for {len(props)} players (Requests remaining: {self.requests_remaining})")
                # Merge into all_props
                for player, stats in props.items():
                    if player not in all_props:
                        all_props[player] = {}
                    all_props[player].update(stats)
            else:
                print(f"  No props available (Requests remaining: {self.requests_remaining})")

            # Rate limit: delay between requests
            if i < len(games):
                time.sleep(delay)

        # Track how many games actually had props
        self.games_with_props = games_with_props_count

        print(f"\n{'='*60}")
        print(f"Games scheduled: {self.games_scheduled}")
        print(f"Games with props: {self.games_with_props}")
        print(f"Total players with props: {len(all_props)}")
        print(f"API Requests Remaining: {self.requests_remaining}/20,000 (20K Plan)")
        print(f"{'='*60}\n")

        return all_props

    def get_all_team_totals(self, delay=0.2):
        """
        Get team totals for all today's games
        Returns dict: {team_name: line}

        Args:
            delay: Seconds to wait between API calls (default 0.2s = 5 req/sec for paid tier)
        """
        print("\n" + "="*60)
        print("Fetching Team Totals from The Odds API")
        print("="*60)

        # Step 1: Get today's games
        games = self.get_todays_games()

        if not games:
            print("No games found")
            return {}

        # Step 2: Fetch team totals for each game
        all_team_totals = {}
        games_with_totals_count = 0

        for i, game in enumerate(games, 1):
            event_id = game.get('id')
            home_team = game.get('home_team', 'Unknown')
            away_team = game.get('away_team', 'Unknown')

            print(f"\n[{i}/{len(games)}] {away_team} @ {home_team}")

            team_totals = self.get_team_totals_for_game(event_id)

            if team_totals:
                games_with_totals_count += 1
                print(f"  Found team totals for {len(team_totals)} teams (Requests remaining: {self.requests_remaining})")
                # Merge into all_team_totals
                all_team_totals.update(team_totals)
            else:
                print(f"  No team totals available (Requests remaining: {self.requests_remaining})")

            # Rate limit: delay between requests
            if i < len(games):
                time.sleep(delay)

        print(f"\n{'='*60}")
        print(f"Games with team totals: {games_with_totals_count}")
        print(f"Total teams with lines: {len(all_team_totals)}")
        print(f"API Requests Remaining: {self.requests_remaining}/20,000 (20K Plan)")
        print(f"{'='*60}\n")

        return all_team_totals


def main():
    """Test the odds fetcher"""
    print("\n🏀 Testing Odds Fetcher Module")

    try:
        fetcher = OddsFetcher()
        props = fetcher.get_all_player_props()

        # Show sample
        print("\nSample player props:")
        for i, (player, stats) in enumerate(list(props.items())[:5], 1):
            print(f"\n{i}. {player}:")
            for stat, line in stats.items():
                print(f"   {stat}: {line}")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
