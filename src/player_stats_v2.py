"""
Player Stats v2 - Correct Floor Calculation
Fetches player game history from NBA API and calculates 10th percentile floor
"""

from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import time
import signal
from typing import Dict, List, Optional
import numpy as np


class TimeoutException(Exception):
    """Exception raised when operation times out"""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal"""
    raise TimeoutException("Operation timed out")


class PlayerStatsAnalyzer:
    """Analyze player game history and calculate floors"""

    # Stats we track
    STATS = ['PTS', 'REB', 'AST', 'FG3M']

    def __init__(self, season: str = '2025-26', min_games: int = 6, max_games: int = 20):
        """
        Args:
            season: NBA season (e.g., '2025-26')
            min_games: Minimum games required to analyze
            max_games: Maximum games to look back
        """
        self.season = season
        self.min_games = min_games
        self.max_games = max_games
        self.all_players = players.get_players()

    def find_player_id(self, player_name: str) -> Optional[int]:
        """Find NBA API player ID by name"""
        matches = [p for p in self.all_players if p['full_name'] == player_name]
        if matches:
            return matches[0]['id']
        return None

    def get_player_game_history(self, player_name: str) -> Optional[Dict]:
        """
        Get recent game history for a player

        Args:
            player_name: Full player name (e.g., "Jalen Brunson")

        Returns:
            Dict with game stats or None if player not found/insufficient games:
            {
                'player_name': str,
                'player_id': int,
                'games': int,
                'PTS': [values],
                'REB': [values],
                'AST': [values],
                'FG3M': [values]
            }
        """
        player_id = self.find_player_id(player_name)
        if not player_id:
            return None

        try:
            # Set 10 second timeout for NBA API call
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)

            try:
                # Fetch game log
                gamelog = playergamelog.PlayerGameLog(
                    player_id=player_id,
                    season=self.season,
                    season_type_all_star='Regular Season'
                )

                df = gamelog.get_data_frames()[0]
            finally:
                # Cancel the alarm
                signal.alarm(0)

            # Check minimum games requirement
            if len(df) < self.min_games:
                return None

            # Get last N games
            recent = df.head(self.max_games)

            # Extract team abbreviation from most recent game's MATCHUP
            # Format is like "NYK vs. BOS" or "NYK @ BOS" where first team is player's team
            team_abbr = None
            try:
                if 'MATCHUP' in recent.columns and len(recent) > 0:
                    matchup = recent.iloc[0]['MATCHUP']
                    # Extract first team abbreviation (before vs. or @)
                    if matchup and isinstance(matchup, str):
                        team_abbr = matchup.split()[0]
            except Exception as e:
                # If team extraction fails, just continue without it
                pass

            return {
                'player_name': player_name,
                'player_id': player_id,
                'team_abbr': team_abbr,
                'games': len(recent),
                'PTS': recent['PTS'].tolist(),
                'REB': recent['REB'].tolist(),
                'AST': recent['AST'].tolist(),
                'FG3M': recent['FG3M'].tolist()
            }

        except TimeoutException:
            print(f"    Timeout fetching stats for {player_name} (>10s)")
            return None
        except Exception as e:
            print(f"    Error fetching stats for {player_name}: {e}")
            return None

    def calculate_floor(self, values: List[int]) -> int:
        """
        Calculate the floor (minimum value = 100% hit rate)

        Args:
            values: List of stat values from recent games

        Returns:
            Floor value (minimum)

        Examples:
            - Any number of games: floor = min value (100% hit rate)
        """
        if not values:
            return 0

        # Simply return the minimum value for 100% hit rate
        return min(values)

    def analyze_player(self, player_name: str) -> Optional[Dict]:
        """
        Analyze a player and calculate floors for all stats

        Args:
            player_name: Full player name

        Returns:
            Dict with player info and floors, or None if insufficient data:
            {
                'player_name': str,
                'games': int,
                'floors': {
                    'PTS': int,
                    'REB': int,
                    'AST': int,
                    'FG3M': int
                },
                'history': {
                    'PTS': [values],
                    'REB': [values],
                    ...
                }
            }
        """
        history = self.get_player_game_history(player_name)

        if not history:
            return None

        # Calculate floors
        floors = {}
        for stat in self.STATS:
            values = history[stat]
            floors[stat] = self.calculate_floor(values)

        return {
            'player_name': player_name,
            'team_abbr': history.get('team_abbr'),
            'games': history['games'],
            'floors': floors,
            'history': {stat: history[stat] for stat in self.STATS}
        }

    def analyze_multiple_players(
        self,
        player_names: List[str],
        delay: float = 0.6,
        verbose: bool = True
    ) -> Dict[str, Dict]:
        """
        Analyze multiple players with rate limiting

        Args:
            player_names: List of player names to analyze
            delay: Seconds between API calls
            verbose: Print progress

        Returns:
            Dict mapping player names to their analysis results
        """
        results = {}

        if verbose:
            print(f"\nAnalyzing {len(player_names)} players...")

        for i, player_name in enumerate(player_names, 1):
            if verbose:
                print(f"  [{i}/{len(player_names)}] {player_name}...", end=' ')

            analysis = self.analyze_player(player_name)

            if analysis:
                results[player_name] = analysis
                if verbose:
                    print(f"{analysis['games']} games ✓")
            else:
                if verbose:
                    print("SKIP")

            # Rate limit
            if i < len(player_names):
                time.sleep(delay)

        if verbose:
            print(f"\n✓ Analyzed {len(results)}/{len(player_names)} players\n")

        return results


def main():
    """Test the player stats analyzer"""
    from dotenv import load_dotenv
    load_dotenv()

    print("\n🏀 Testing Player Stats Analyzer")

    analyzer = PlayerStatsAnalyzer(season='2025-26')

    # Test with Jalen Brunson
    print("\nTesting with Jalen Brunson:")
    result = analyzer.analyze_player("Jalen Brunson")

    if result:
        print(f"\nPlayer: {result['player_name']}")
        print(f"Games analyzed: {result['games']}")
        print(f"\nFloors (10th percentile):")
        for stat, floor in result['floors'].items():
            values = result['history'][stat]
            print(f"  {stat}: {floor} (from {sorted(values)})")
    else:
        print("Could not analyze player")


if __name__ == "__main__":
    main()
