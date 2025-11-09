"""
Baby Run-Through: Single Player Example
Demonstrates the full 90%er workflow:
1. Get player's season stats
2. Calculate 10th percentile (90%er floor) for each stat
3. Compare to mock betting line
4. Identify value opportunities
"""

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import numpy as np


def get_player_stats(player_name, season='2025-26'):
    """Get all games for a player this season"""
    print(f"\n{'='*60}")
    print(f"Step 1: Fetching data for {player_name}")
    print(f"{'='*60}")

    # Find player
    all_players = players.get_players()
    player = [p for p in all_players if player_name.lower() in p['full_name'].lower()]

    if not player:
        print(f"Player not found: {player_name}")
        return None

    player = player[0]
    print(f"Found: {player['full_name']} (ID: {player['id']})")

    # Get game log
    gamelog = playergamelog.PlayerGameLog(
        player_id=player['id'],
        season=season,
        season_type_all_star='Regular Season'
    )

    df = gamelog.get_data_frames()[0]

    # Filter to only games already played
    df['GAME_DATE_DT'] = pd.to_datetime(df['GAME_DATE'])
    today = pd.Timestamp.now()
    df = df[df['GAME_DATE_DT'] <= today].copy()

    print(f"Games played this season: {len(df)}")

    return {
        'player': player['full_name'],
        'games': df
    }


def calculate_90er_floors(games_df, stats_to_analyze):
    """
    Calculate the 10th percentile (90%er floor) for each stat
    This is the value the player hits or exceeds in 90% of games
    """
    print(f"\n{'='*60}")
    print(f"Step 2: Calculating 90%er Floors (10th percentile)")
    print(f"{'='*60}")

    floors = {}

    for stat in stats_to_analyze:
        if stat not in games_df.columns:
            print(f"Stat {stat} not found in data")
            continue

        values = games_df[stat].values

        # Calculate 10th percentile
        # This means: player is AT LEAST this good in 90% of games
        percentile_10 = np.percentile(values, 10)

        # Round UP to next whole number (ceiling)
        # e.g., 29.3 becomes 30, 1.9 becomes 2
        if stat in ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M']:
            percentile_10 = np.ceil(percentile_10)

        floors[stat] = {
            'floor': percentile_10,
            'avg': values.mean(),
            'min': values.min(),
            'max': values.max(),
            'recent_games': values[:5].tolist()  # Last 5 games
        }

        print(f"\n{stat}:")
        print(f"  90%er Floor: {percentile_10:.1f} (hits this or better in 90% of games)")
        print(f"  Average: {values.mean():.1f}")
        print(f"  Range: {values.min():.0f} - {values.max():.0f}")
        print(f"  Last 5 games: {values[:5].tolist()}")

    return floors


def compare_to_betting_lines(floors, mock_lines):
    """
    Compare 90%er floors to betting lines
    Flag value when floor is within 10% range of the line
    """
    print(f"\n{'='*60}")
    print(f"Step 3: Comparing to Betting Lines")
    print(f"{'='*60}")

    value_opportunities = []
    tolerance = 0.10  # 10%

    for stat, line in mock_lines.items():
        if stat not in floors:
            continue

        floor = floors[stat]['floor']

        # Calculate 10% range around the line
        lower_bound = line * (1 - tolerance)
        upper_bound = line * (1 + tolerance)

        # Check if floor is above lower bound (Over has value)
        has_value = floor >= lower_bound

        print(f"\n{stat}:")
        print(f"  Betting Line: {line}")
        print(f"  90%er Floor: {floor:.1f}")
        print(f"  10% Range: {lower_bound:.1f} - {upper_bound:.1f}")

        if has_value:
            confidence = "HIGH" if floor >= line else "MEDIUM"
            print(f"  ✅ OVER VALUE DETECTED ({confidence})")
            print(f"     → Player hits {floor:.1f}+ in 90% of games")
            print(f"     → Line is at {line}")

            value_opportunities.append({
                'stat': stat,
                'line': line,
                'floor': floor,
                'confidence': confidence,
                'range': f"{lower_bound:.1f} - {upper_bound:.1f}"
            })
        else:
            print(f"  ❌ No value (floor {floor:.1f} is below range)")

    return value_opportunities


def main():
    """Run baby example with one player"""
    print("\n🏀 NBA 90%ers - Baby Run-Through")
    print("Testing with: Shai Gilgeous-Alexander\n")

    # Step 1: Get player stats
    player_data = get_player_stats("Shai Gilgeous-Alexander")

    if not player_data:
        return

    # Step 2: Calculate 90%er floors for key stats
    stats_to_check = ['PTS', 'REB', 'AST', 'FG3M', 'STL']
    floors = calculate_90er_floors(player_data['games'], stats_to_check)

    # Step 3: Mock betting lines (these would come from The Odds API)
    # Let's use realistic lines based on what we saw earlier
    mock_betting_lines = {
        'PTS': 30.5,   # His floor was ~23 from 10 games
        'REB': 5.5,    # Let's see what his floor is
        'AST': 6.5,    # Let's see
        'FG3M': 2.5,   # Threes made
        'STL': 1.5     # Steals
    }

    print(f"\n{'='*60}")
    print("Mock Betting Lines (would come from The Odds API):")
    print(f"{'='*60}")
    for stat, line in mock_betting_lines.items():
        print(f"  {stat}: {line}")

    # Step 4: Find value opportunities
    value_opps = compare_to_betting_lines(floors, mock_betting_lines)

    # Step 5: Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    if value_opps:
        print(f"\n✅ Found {len(value_opps)} value opportunity(ies):\n")
        for opp in value_opps:
            print(f"  {opp['stat']}: Over {opp['line']} ({opp['confidence']} confidence)")
            print(f"    Floor: {opp['floor']:.1f} | Range: {opp['range']}")
    else:
        print("\n❌ No value opportunities found with current lines")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
