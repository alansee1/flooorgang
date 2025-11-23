"""
NFL Stats Analyzer
Analyzes NFL player and team statistics to calculate floors/ceilings (100%ers)
Uses nflreadpy to fetch historical game data from 2025 season
"""

import nflreadpy as nfl
import polars as pl
from typing import Dict, List, Optional


class NFLStatsAnalyzer:
    """Analyzes NFL player and team stats to find floors for betting props"""

    def __init__(self, season: int = 2025):
        """
        Args:
            season: NFL season year (default 2025 for current season)
        """
        self.season = season
        self.player_stats = None
        self.schedules = None

    def load_player_stats(self):
        """Load all player stats for the season"""
        if self.player_stats is None:
            print(f"Loading {self.season} NFL player stats...")
            self.player_stats = nfl.load_player_stats([self.season])
            print(f"✓ Loaded {len(self.player_stats)} player-game records")

    def load_schedules(self):
        """Load schedules (for team scoring data)"""
        if self.schedules is None:
            print(f"Loading {self.season} NFL schedules...")
            self.schedules = nfl.load_schedules([self.season])
            print(f"✓ Loaded schedules")

    def get_player_floor(
        self,
        player_name: str,
        stat_column: str,
        min_games: int = 4
    ) -> Optional[Dict]:
        """
        Calculate floor for a specific player and stat

        Args:
            player_name: Player's display name
            stat_column: Stat to analyze (e.g., 'passing_yards', 'rushing_yards')
            min_games: Minimum number of games required (default 4)

        Returns:
            Dict with {floor, games, history, average, maximum} or None if not found
        """
        self.load_player_stats()

        # Filter to this player's games
        player_games = self.player_stats.filter(
            pl.col('player_display_name') == player_name
        )

        if len(player_games) == 0:
            return None

        # Get stat values
        stat_values = player_games.select(stat_column).to_series().to_list()

        if not stat_values or len(stat_values) == 0:
            return None

        # Require minimum sample size
        if len(stat_values) < min_games:
            return None

        # Calculate floor (MINIMUM value)
        floor = min(stat_values)

        return {
            'floor': floor,
            'games': len(stat_values),
            'history': stat_values,
            'average': sum(stat_values) / len(stat_values),
            'maximum': max(stat_values)
        }

    def get_team_floor_ceiling(
        self,
        team_abbr: str,
        min_games: int = 4
    ) -> Optional[Dict]:
        """
        Calculate floor and ceiling for a team's scoring

        Args:
            team_abbr: Team abbreviation (e.g., 'BUF', 'HOU')
            min_games: Minimum number of games required (default 4)

        Returns:
            Dict with {floor, ceiling, games, history, average} or None if not found
        """
        self.load_schedules()

        # Get games where team played (home or away)
        home_games = self.schedules.filter(pl.col('home_team') == team_abbr)
        away_games = self.schedules.filter(pl.col('away_team') == team_abbr)

        # Get scores (filter out None for future games)
        home_scores = [s for s in home_games.select('home_score').to_series().to_list() if s is not None]
        away_scores = [s for s in away_games.select('away_score').to_series().to_list() if s is not None]

        all_scores = home_scores + away_scores

        if not all_scores or len(all_scores) == 0:
            return None

        # Require minimum sample size
        if len(all_scores) < min_games:
            return None

        return {
            'floor': min(all_scores),
            'ceiling': max(all_scores),
            'games': len(all_scores),
            'history': all_scores,
            'average': sum(all_scores) / len(all_scores)
        }

    def analyze_players_batch(
        self,
        player_names: List[str],
        stat_column: str
    ) -> Dict[str, Dict]:
        """
        Analyze multiple players at once for a specific stat

        Args:
            player_names: List of player names
            stat_column: Stat to analyze

        Returns:
            Dict mapping player_name -> {floor, games, history, average, maximum}
        """
        results = {}

        for player_name in player_names:
            floor_data = self.get_player_floor(player_name, stat_column)
            if floor_data:
                results[player_name] = floor_data

        return results


def main():
    """Test the analyzer"""
    analyzer = NFLStatsAnalyzer(season=2025)

    # Test player
    print("Testing Nick Chubb rushing yards...")
    result = analyzer.get_player_floor('Nick Chubb', 'rushing_yards')
    if result:
        print(f"  Floor: {result['floor']} yards")
        print(f"  Games: {result['games']}")
        print(f"  Average: {result['average']:.1f}")

    # Test team
    print("\nTesting Buffalo Bills scoring...")
    result = analyzer.get_team_floor_ceiling('BUF')
    if result:
        print(f"  Floor: {result['floor']} points")
        print(f"  Ceiling: {result['ceiling']} points")
        print(f"  Games: {result['games']}")


if __name__ == "__main__":
    main()
