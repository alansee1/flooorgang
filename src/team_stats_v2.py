"""
Team Stats v2 - Team Total Points Analysis
Fetches team game history and calculates floor (min) and ceiling (max) points
"""

from nba_api.stats.endpoints import leaguegamefinder
from typing import Dict, List, Optional
import time
import signal


class TimeoutException(Exception):
    """Exception raised when operation times out"""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal"""
    raise TimeoutException("Operation timed out")


class TeamStatsAnalyzer:
    """Analyze team scoring patterns for OVER/UNDER bets"""

    # NBA team name to ID mapping
    TEAM_IDS = {
        'Atlanta Hawks': 1610612737,
        'Boston Celtics': 1610612738,
        'Brooklyn Nets': 1610612751,
        'Charlotte Hornets': 1610612766,
        'Chicago Bulls': 1610612741,
        'Cleveland Cavaliers': 1610612739,
        'Dallas Mavericks': 1610612742,
        'Denver Nuggets': 1610612743,
        'Detroit Pistons': 1610612765,
        'Golden State Warriors': 1610612744,
        'Houston Rockets': 1610612745,
        'Indiana Pacers': 1610612754,
        'LA Clippers': 1610612746,
        'Los Angeles Lakers': 1610612747,
        'Memphis Grizzlies': 1610612763,
        'Miami Heat': 1610612748,
        'Milwaukee Bucks': 1610612749,
        'Minnesota Timberwolves': 1610612750,
        'New Orleans Pelicans': 1610612740,
        'New York Knicks': 1610612752,
        'Oklahoma City Thunder': 1610612760,
        'Orlando Magic': 1610612753,
        'Philadelphia 76ers': 1610612755,
        'Phoenix Suns': 1610612756,
        'Portland Trail Blazers': 1610612757,
        'Sacramento Kings': 1610612758,
        'San Antonio Spurs': 1610612759,
        'Toronto Raptors': 1610612761,
        'Utah Jazz': 1610612762,
        'Washington Wizards': 1610612764,
    }

    def __init__(self, season: str = '2025-26', min_games: int = 6, max_games: int = 20):
        """
        Args:
            season: NBA season (e.g., '2025-26')
            min_games: Minimum games required
            max_games: Maximum games to look back
        """
        self.season = season
        self.min_games = min_games
        self.max_games = max_games

    def get_team_id(self, team_name: str) -> Optional[int]:
        """Get NBA API team ID from team name"""
        return self.TEAM_IDS.get(team_name)

    def get_team_game_history(self, team_name: str) -> Optional[Dict]:
        """
        Get recent scoring history for a team

        Args:
            team_name: Full team name (e.g., "New York Knicks")

        Returns:
            Dict with team stats or None if insufficient data:
            {
                'team_name': str,
                'team_id': int,
                'games': int,
                'points': [values],
                'floor': int (minimum points),
                'ceiling': int (maximum points)
            }
        """
        team_id = self.get_team_id(team_name)
        if not team_id:
            return None

        try:
            # Set 10 second timeout for NBA API call
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)

            try:
                # Fetch game log using LeagueGameFinder
                gamefinder = leaguegamefinder.LeagueGameFinder(
                    team_id_nullable=team_id,
                    season_nullable=self.season,
                    season_type_nullable='Regular Season'
                )

                games_df = gamefinder.get_data_frames()[0]
            finally:
                # Cancel the alarm
                signal.alarm(0)

            # Check minimum games
            if len(games_df) < self.min_games:
                return None

            # Get last N games
            recent = games_df.head(self.max_games)
            points = recent['PTS'].tolist()

            return {
                'team_name': team_name,
                'team_id': team_id,
                'games': len(recent),
                'points': points,
                'floor': min(points),     # For OVER bets
                'ceiling': max(points)    # For UNDER bets
            }

        except TimeoutException:
            print(f"    Timeout fetching stats for {team_name} (>10s)")
            return None
        except Exception as e:
            print(f"    Error fetching stats for {team_name}: {e}")
            return None

    def analyze_multiple_teams(
        self,
        team_names: List[str],
        delay: float = 0.6,
        verbose: bool = True
    ) -> Dict[str, Dict]:
        """
        Analyze multiple teams with rate limiting

        Args:
            team_names: List of team names to analyze
            delay: Seconds between API calls
            verbose: Print progress

        Returns:
            Dict mapping team names to their analysis results
        """
        results = {}

        if verbose:
            print(f"\nAnalyzing {len(team_names)} teams...")

        for i, team_name in enumerate(team_names, 1):
            if verbose:
                print(f"  [{i}/{len(team_names)}] {team_name}...", end=' ')

            analysis = self.get_team_game_history(team_name)

            if analysis:
                results[team_name] = analysis
                if verbose:
                    print(f"{analysis['games']} games (floor: {analysis['floor']}, ceiling: {analysis['ceiling']}) ✓")
            else:
                if verbose:
                    print("SKIP")

            # Rate limit
            if i < len(team_names):
                time.sleep(delay)

        if verbose:
            print(f"\n✓ Analyzed {len(results)}/{len(team_names)} teams\n")

        return results


def main():
    """Test the team stats analyzer"""
    from dotenv import load_dotenv
    load_dotenv()

    print("\n🏀 Testing Team Stats Analyzer")

    analyzer = TeamStatsAnalyzer(season='2025-26')

    # Test with a few teams
    teams = ['New York Knicks', 'Memphis Grizzlies', 'Denver Nuggets']
    results = analyzer.analyze_multiple_teams(teams)

    print("\nResults:")
    for team, stats in results.items():
        print(f"\n{team}:")
        print(f"  Games: {stats['games']}")
        print(f"  Points: {sorted(stats['points'])}")
        print(f"  Floor: {stats['floor']} (for OVER bets)")
        print(f"  Ceiling: {stats['ceiling']} (for UNDER bets)")


if __name__ == "__main__":
    main()
