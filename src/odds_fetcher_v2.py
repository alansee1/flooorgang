"""
Odds Fetcher v2 - Alternate Lines Edition
Fetches alternate betting lines from The Odds API (DraftKings)
"""

import requests
import os
import time
from typing import Dict, List, Optional


class OddsFetcher:
    """Fetch alternate betting lines from The Odds API"""

    # Market mappings for NBA
    MARKETS = {
        'player_points_alternate': 'PTS',
        'player_rebounds_alternate': 'REB',
        'player_assists_alternate': 'AST',
        'player_threes_alternate': 'FG3M',
        'player_steals_alternate': 'STL',
        'player_blocks_alternate': 'BLK'
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.sport = 'basketball_nba'
        self.bookmaker = 'draftkings'  # DraftKings has the best alternate line coverage
        self.requests_remaining = None

        if not self.api_key:
            raise ValueError("API key required. Set ODDS_API_KEY env var or pass to constructor")

    def get_todays_games(self) -> List[Dict]:
        """
        Get list of today's NBA games (in US Eastern Time)

        Returns:
            List of game dicts with id, home_team, away_team, commence_time
        """
        from datetime import datetime, timezone, timedelta
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
            raise Exception(f"Error fetching games: {response.status_code} - {response.text}")

        all_games = response.json()

        # Filter to only today's games (in US Eastern Time)
        eastern = ZoneInfo("America/New_York")
        now = datetime.now(eastern)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        games = []
        for game in all_games:
            commence_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
            commence_time_et = commence_time.astimezone(eastern)
            if today_start <= commence_time_et < today_end:
                games.append(game)

        print(f"✓ Found {len(games)} NBA games today (ET)")
        print(f"  API Requests remaining: {self.requests_remaining}/20,000")

        return games

    def get_alternate_lines_for_game(self, event_id: str) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get alternate lines for all players in a game

        Args:
            event_id: The Odds API event ID

        Returns:
            Dict structure:
            {
                'Player Name': {
                    'PTS': [{'line': 14.5, 'odds': -1840}, {'line': 17.5, 'odds': -800}, ...],
                    'REB': [{'line': 2.5, 'odds': -230}, ...],
                    ...
                }
            }
        """
        url = f"{self.base_url}/sports/{self.sport}/events/{event_id}/odds"

        # Request all alternate markets
        markets_str = ','.join(self.MARKETS.keys())

        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': markets_str,
            'oddsFormat': 'american'
        }

        response = requests.get(url, params=params)
        self.requests_remaining = response.headers.get('x-requests-remaining')

        if response.status_code != 200:
            print(f"⚠️  Warning: Could not fetch props for event {event_id}: {response.text}")
            return {}

        data = response.json()
        return self._parse_alternate_lines(data)

    def _parse_alternate_lines(self, event_data: Dict) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Parse alternate lines from API response

        Returns:
            {player_name: {stat: [{'line': X, 'odds': Y}]}}
        """
        player_lines = {}

        if 'bookmakers' not in event_data or not event_data['bookmakers']:
            return player_lines

        # Find DraftKings bookmaker
        draftkings = None
        for bookmaker in event_data['bookmakers']:
            if bookmaker['key'] == self.bookmaker:
                draftkings = bookmaker
                break

        if not draftkings or 'markets' not in draftkings:
            return player_lines

        # Parse each market
        for market in draftkings['markets']:
            market_key = market.get('key')
            stat_name = self.MARKETS.get(market_key)

            if not stat_name:
                continue

            # Process all "Over" outcomes
            for outcome in market.get('outcomes', []):
                if outcome.get('name') != 'Over':
                    continue

                player_name = outcome.get('description', '').strip()
                line = outcome.get('point')
                odds = outcome.get('price')

                if not player_name or line is None or odds is None:
                    continue

                # Initialize player if not seen
                if player_name not in player_lines:
                    player_lines[player_name] = {}

                # Initialize stat if not seen
                if stat_name not in player_lines[player_name]:
                    player_lines[player_name][stat_name] = []

                # Add this line
                player_lines[player_name][stat_name].append({
                    'line': line,
                    'odds': odds
                })

        return player_lines

    def get_all_alternate_lines(self, delay: float = 0.2) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get alternate lines for all today's games

        Args:
            delay: Seconds to wait between API calls (default 0.2s for paid tier)

        Returns:
            Combined dict of all players across all games:
            {player_name: {stat: [{'line': X, 'odds': Y}]}}
        """
        print("\n" + "="*70)
        print("Fetching Alternate Lines from DraftKings")
        print("="*70 + "\n")

        # Get today's games
        games = self.get_todays_games()

        if not games:
            print("No games found")
            return {}

        # Fetch alternate lines for each game
        all_lines = {}

        for i, game in enumerate(games, 1):
            event_id = game['id']
            home = game['home_team']
            away = game['away_team']

            print(f"\n[{i}/{len(games)}] {away} @ {home}")

            game_lines = self.get_alternate_lines_for_game(event_id)

            if game_lines:
                print(f"  ✓ Found alternate lines for {len(game_lines)} players")

                # Merge into all_lines
                for player, stats in game_lines.items():
                    if player not in all_lines:
                        all_lines[player] = {}

                    for stat, lines in stats.items():
                        if stat not in all_lines[player]:
                            all_lines[player][stat] = []
                        all_lines[player][stat].extend(lines)
            else:
                print(f"  ⚠️  No alternate lines available")

            # Rate limit
            if i < len(games):
                time.sleep(delay)

        print(f"\n{'='*70}")
        print(f"Total players with alternate lines: {len(all_lines)}")
        print(f"API Requests remaining: {self.requests_remaining}/20,000")
        print(f"{'='*70}\n")

        return all_lines

    def get_alternate_team_totals(self, delay: float = 0.2) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get alternate team totals for all today's games

        Args:
            delay: Seconds to wait between API calls

        Returns:
            Dict structure:
            {
                'Team Name': {
                    'over': [{'line': 101.5, 'odds': -517}, ...],
                    'under': [{'line': 101.5, 'odds': 365}, ...]
                }
            }
        """
        print("\n" + "="*70)
        print("Fetching Alternate Team Totals from DraftKings")
        print("="*70 + "\n")

        # Get today's games
        games = self.get_todays_games()

        if not games:
            print("No games found")
            return {}

        # Fetch alternate team totals for each game
        all_team_lines = {}

        for i, game in enumerate(games, 1):
            event_id = game['id']
            home = game['home_team']
            away = game['away_team']

            print(f"\n[{i}/{len(games)}] {away} @ {home}")

            # Fetch alternate_team_totals market
            url = f"{self.base_url}/sports/{self.sport}/events/{event_id}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'alternate_team_totals',
                'oddsFormat': 'american'
            }

            response = requests.get(url, params=params)
            self.requests_remaining = response.headers.get('x-requests-remaining')

            if response.status_code != 200:
                print(f"  ⚠️  Could not fetch team totals")
                continue

            data = response.json()

            # Parse team totals
            team_lines = {}
            for bookmaker in data.get('bookmakers', []):
                if bookmaker['key'] == self.bookmaker:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'alternate_team_totals':
                            for outcome in market.get('outcomes', []):
                                team = outcome['description']
                                bet_type = outcome['name']
                                line = outcome['point']
                                odds = outcome['price']

                                if team not in team_lines:
                                    team_lines[team] = {'over': [], 'under': []}

                                if bet_type == 'Over':
                                    team_lines[team]['over'].append({'line': line, 'odds': odds})
                                else:
                                    team_lines[team]['under'].append({'line': line, 'odds': odds})

            if team_lines:
                print(f"  ✓ Found team totals for {len(team_lines)} teams")
                # Merge into all_team_lines
                all_team_lines.update(team_lines)
            else:
                print(f"  ⚠️  No team totals available")

            # Rate limit
            if i < len(games):
                time.sleep(delay)

        print(f"\n{'='*70}")
        print(f"Total teams with alternate lines: {len(all_team_lines)}")
        print(f"API Requests remaining: {self.requests_remaining}/20,000")
        print(f"{'='*70}\n")

        return all_team_lines


def main():
    """Test the odds fetcher"""
    from dotenv import load_dotenv
    load_dotenv()

    print("\n🏀 Testing Alternate Lines Odds Fetcher")

    try:
        fetcher = OddsFetcher()
        all_lines = fetcher.get_all_alternate_lines()

        # Show sample for first player
        if all_lines:
            print("\nSample - First player's alternate lines:")
            player_name = list(all_lines.keys())[0]
            print(f"\n{player_name}:")

            for stat, lines in all_lines[player_name].items():
                print(f"\n  {stat}:")
                for line_data in sorted(lines, key=lambda x: x['line'])[:5]:  # Show first 5
                    print(f"    {line_data['line']} Over @ {line_data['odds']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
