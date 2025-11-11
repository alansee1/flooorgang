"""
Team Stats Module
Fetches team game logs and calculates floor/ceiling for team totals betting
"""

from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
import numpy as np


def get_team_stats(team_name, season='2025-26'):
    """
    Get recent games for a team this season

    Args:
        team_name: Team name (e.g., "Lakers", "Los Angeles Lakers")
        season: NBA season (default: 2025-26)

    Returns:
        Dict with team info and games DataFrame, or None if not found
    """
    # Find team
    all_teams = teams.get_teams()
    team = None

    # Try exact match first
    for t in all_teams:
        if team_name.lower() == t['full_name'].lower() or team_name.lower() == t['nickname'].lower():
            team = t
            break

    # If no exact match, try partial match
    if not team:
        for t in all_teams:
            if team_name.lower() in t['full_name'].lower() or team_name.lower() in t['nickname'].lower():
                team = t
                break

    if not team:
        print(f"Team not found: {team_name}")
        return None

    # Get game log using LeagueGameFinder
    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team['id'],
            season_nullable=season
        )

        df = gamefinder.get_data_frames()[0]

        # Filter to only games already played
        df['GAME_DATE_DT'] = pd.to_datetime(df['GAME_DATE'])
        today = pd.Timestamp.now()
        df = df[df['GAME_DATE_DT'] <= today].copy()

        print(f"Games played this season: {len(df)}")

        return {
            'team': team['full_name'],
            'nickname': team['nickname'],
            'games': df
        }
    except Exception as e:
        print(f"Error fetching team stats for {team_name}: {e}")
        return None


def calculate_team_floors_ceilings(games_df):
    """
    Calculate floor (minimum) and ceiling (maximum) for team points

    Args:
        games_df: DataFrame with team game logs

    Returns:
        Dict with floor, ceiling, avg, min, max for team points
    """
    if games_df.empty:
        return None

    # Team points are in the 'PTS' column
    if 'PTS' not in games_df.columns:
        print("PTS column not found in team game log")
        return None

    values = games_df['PTS'].values

    # Floor = absolute minimum (worst scoring game)
    # Ceiling = absolute maximum (best scoring game)
    floor_value = values.min()
    ceiling_value = values.max()

    return {
        'floor': floor_value,
        'ceiling': ceiling_value,
        'avg': values.mean(),
        'min': values.min(),
        'max': values.max(),
        'games_played': len(values),
        'recent_games': values[:5].tolist()  # Last 5 games
    }


def main():
    """Test the team stats module"""
    print("\n🏀 Testing Team Stats Module\n")

    # Test with Lakers
    test_teams = ["Lakers", "Celtics"]

    for team_name in test_teams:
        print(f"{'='*60}")
        print(f"Fetching stats for {team_name}")
        print(f"{'='*60}")

        team_data = get_team_stats(team_name)

        if not team_data:
            print(f"❌ Could not fetch data for {team_name}\n")
            continue

        print(f"Team: {team_data['team']}")
        print(f"Games played: {len(team_data['games'])}")

        stats = calculate_team_floors_ceilings(team_data['games'])

        if stats:
            print(f"\nTeam Points Stats:")
            print(f"  Floor (worst game): {stats['floor']:.0f}")
            print(f"  Ceiling (best game): {stats['ceiling']:.0f}")
            print(f"  Average: {stats['avg']:.1f}")
            print(f"  Last 5 games: {stats['recent_games']}")

            # Mock betting line
            mock_line = 112.5
            lower_bound = mock_line * 0.9
            upper_bound = mock_line * 1.1

            print(f"\nMock Betting Line: {mock_line}")
            print(f"  10% Range: {lower_bound:.1f} - {upper_bound:.1f}")

            # Check OVER value
            if stats['floor'] >= lower_bound:
                print(f"  ✅ OVER has value (floor {stats['floor']:.0f} >= {lower_bound:.1f})")
            else:
                print(f"  ❌ No OVER value (floor {stats['floor']:.0f} < {lower_bound:.1f})")

            # Check UNDER value
            if stats['ceiling'] <= upper_bound:
                print(f"  ✅ UNDER has value (ceiling {stats['ceiling']:.0f} <= {upper_bound:.1f})")
            else:
                print(f"  ❌ No UNDER value (ceiling {stats['ceiling']:.0f} > {upper_bound:.1f})")

        print()


if __name__ == "__main__":
    main()
