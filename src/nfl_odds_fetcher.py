"""
NFL Odds Fetcher
Fetches NFL alternate betting lines from The Odds API (DraftKings)
"""

import requests
import os
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class NFLOddsFetcher:
    """Fetch NFL alternate betting lines from The Odds API"""

    # Market mappings for NFL
    PLAYER_MARKETS = {
        'player_pass_yds_alternate': 'Pass Yds',
        'player_rush_yds_alternate': 'Rush Yds',
        'player_reception_yds_alternate': 'Rec Yds',
        'player_receptions_alternate': 'Receptions',
        'player_pass_tds_alternate': 'Pass TDs',
        'player_pass_completions_alternate': 'Completions',
        'player_pass_attempts_alternate': 'Attempts'
    }

    # Stat column mappings (for stats analyzer)
    STAT_COLUMNS = {
        'Pass Yds': 'passing_yards',
        'Rush Yds': 'rushing_yards',
        'Rec Yds': 'receiving_yards',
        'Receptions': 'receptions',
        'Pass TDs': 'passing_tds',
        'Completions': 'completions',
        'Attempts': 'attempts'
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.sport = 'americanfootball_nfl'
        self.bookmaker = 'draftkings'
        self.requests_remaining = None

        if not self.api_key:
            raise ValueError("API key required. Set ODDS_API_KEY env var or pass to constructor")

    def get_todays_games(self) -> List[Dict]:
        """
        Get list of today's NFL games (in US Eastern Time)

        Returns:
            List of game dicts with id, home_team, away_team, commence_time
        """
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        url = f"{self.base_url}/sports/{self.sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'h2h'
        }

        response = requests.get(url, params=params)
        self.requests_remaining = response.headers.get('x-requests-remaining')

        if response.status_code != 200:
            print(f"❌ Failed to fetch games: {response.status_code}")
            return []

        all_games = response.json()

        # Filter to today's games (in ET)
        et = ZoneInfo("America/New_York")
        now_et = datetime.now(et)
        today_start = now_et.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        todays_games = []
        for game in all_games:
            game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
            game_time_et = game_time.astimezone(et)

            if today_start <= game_time_et < tomorrow_start:
                todays_games.append({
                    'id': game['id'],
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'commence_time': game['commence_time']
                })

        return todays_games

    def get_player_props(self, game_id: str) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get all player prop alternate lines for a game

        Args:
            game_id: Game ID from get_todays_games()

        Returns:
            Dict mapping player_name -> {stat_name -> [{'line': X, 'odds': Y}]}
        """
        player_lines = {}

        for market_key, stat_display in self.PLAYER_MARKETS.items():
            url = f"{self.base_url}/sports/{self.sport}/events/{game_id}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': market_key,
                'oddsFormat': 'american'
            }

            response = requests.get(url, params=params)
            self.requests_remaining = response.headers.get('x-requests-remaining')

            if response.status_code != 200:
                continue

            data = response.json()

            if data.get('bookmakers'):
                for bookmaker in data['bookmakers']:
                    if bookmaker['key'] == self.bookmaker:
                        for market in bookmaker.get('markets', []):
                            for outcome in market.get('outcomes', []):
                                player_name = outcome.get('description')
                                if player_name:
                                    if player_name not in player_lines:
                                        player_lines[player_name] = {}
                                    if stat_display not in player_lines[player_name]:
                                        player_lines[player_name][stat_display] = []

                                    player_lines[player_name][stat_display].append({
                                        'line': outcome.get('point'),
                                        'odds': outcome.get('price')
                                    })

            time.sleep(0.5)  # Be nice to API

        return player_lines

    def get_team_totals(self, game_id: str) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get team total alternate lines for a game

        Args:
            game_id: Game ID from get_todays_games()

        Returns:
            Dict mapping team_name -> {'overs': [...], 'unders': [...]}
        """
        url = f"{self.base_url}/sports/{self.sport}/events/{game_id}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'alternate_team_totals',
            'oddsFormat': 'american'
        }

        response = requests.get(url, params=params)
        self.requests_remaining = response.headers.get('x-requests-remaining')

        if response.status_code != 200:
            return {}

        data = response.json()
        team_lines = {}

        if data.get('bookmakers'):
            for bookmaker in data['bookmakers']:
                if bookmaker['key'] == self.bookmaker:
                    for market in bookmaker.get('markets', []):
                        for outcome in market.get('outcomes', []):
                            team_name = outcome.get('description')
                            bet_type = outcome.get('name')  # 'Over' or 'Under'

                            if team_name:
                                if team_name not in team_lines:
                                    team_lines[team_name] = {'overs': [], 'unders': []}

                                line_data = {
                                    'line': outcome.get('point'),
                                    'odds': outcome.get('price')
                                }

                                if bet_type == 'Over':
                                    team_lines[team_name]['overs'].append(line_data)
                                elif bet_type == 'Under':
                                    team_lines[team_name]['unders'].append(line_data)

        return team_lines


def main():
    """Test the fetcher"""
    fetcher = NFLOddsFetcher()

    print("Fetching today's NFL games...")
    games = fetcher.get_todays_games()
    print(f"✓ Found {len(games)} games today")

    if games:
        game = games[0]
        print(f"\nTesting with: {game['away_team']} @ {game['home_team']}")

        print("\nFetching player props...")
        player_props = fetcher.get_player_props(game['id'])
        print(f"✓ Found props for {len(player_props)} players")

        print("\nFetching team totals...")
        team_totals = fetcher.get_team_totals(game['id'])
        print(f"✓ Found totals for {len(team_totals)} teams")

    print(f"\nAPI requests remaining: {fetcher.requests_remaining}")


if __name__ == "__main__":
    main()
