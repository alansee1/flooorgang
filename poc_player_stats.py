"""
NBA 90%ers Proof of Concept
Analyze player consistency for hitting stat thresholds
"""

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
from datetime import datetime


def find_player(player_name):
    """Find player ID by name"""
    all_players = players.get_players()
    player = [p for p in all_players if player_name.lower() in p['full_name'].lower()]

    if not player:
        print(f"No player found matching '{player_name}'")
        return None

    if len(player) > 1:
        print(f"Multiple players found:")
        for p in player:
            print(f"  - {p['full_name']} (ID: {p['id']})")
        return player[0]

    return player[0]


def get_player_game_log(player_id, season='2025-26'):
    """Get game log for a player in the current season - ONLY actual games played"""
    gamelog = playergamelog.PlayerGameLog(
        player_id=player_id,
        season=season,
        season_type_all_star='Regular Season'
    )

    df = gamelog.get_data_frames()[0]

    # Filter to only games that have actually been played (not future/projected games)
    # Convert GAME_DATE to datetime for comparison
    df['GAME_DATE_DT'] = pd.to_datetime(df['GAME_DATE'])
    today = pd.Timestamp.now()

    # Only keep games that have already occurred
    df = df[df['GAME_DATE_DT'] <= today].copy()

    return df


def calculate_consistency(df, stat_column, threshold, window_size=20):
    """
    Calculate what percentage of games a player hit a threshold

    Args:
        df: DataFrame with game logs
        stat_column: Column name (e.g., 'PTS', 'REB', 'AST')
        threshold: Minimum value to hit (e.g., 25 for 25+ points)
        window_size: Number of recent games to analyze (default 20)

    Returns:
        Dictionary with consistency metrics
    """
    # Sort by game date (most recent first)
    df = df.sort_values('GAME_DATE', ascending=False).copy()

    # Use window_size or all games if fewer than window_size
    games_to_analyze = min(window_size, len(df))
    recent_games = df.head(games_to_analyze)

    # Count games where threshold was hit
    hits = (recent_games[stat_column] >= threshold).sum()
    total_games = len(recent_games)
    consistency_pct = (hits / total_games * 100) if total_games > 0 else 0

    return {
        'stat': stat_column,
        'threshold': threshold,
        'hits': hits,
        'total_games': total_games,
        'consistency_pct': consistency_pct,
        'avg_value': recent_games[stat_column].mean(),
        'max_value': recent_games[stat_column].max(),
        'min_value': recent_games[stat_column].min()
    }


def analyze_player(player_name, thresholds_config, window_size=20, min_consistency=90.0):
    """
    Analyze a player's consistency across multiple stat thresholds

    Args:
        player_name: Player's name (e.g., "LeBron James")
        thresholds_config: Dict of {stat: threshold} e.g., {'PTS': 25, 'REB': 7, 'AST': 7}
        window_size: Number of recent games to analyze
        min_consistency: Minimum consistency % to display (default 90.0)
    """
    # Find player
    player = find_player(player_name)
    if not player:
        return None

    print(f"\n{'='*60}")
    print(f"Analyzing: {player['full_name']}")
    print(f"{'='*60}")

    # Get game log
    df = get_player_game_log(player['id'])

    if df.empty:
        print("No games found for this season")
        return None

    print(f"Total games this season: {len(df)}")
    print(f"Analyzing last {min(window_size, len(df))} games")
    print(f"Filtering for {min_consistency}%+ consistency")
    print(f"{'='*60}\n")

    # Calculate consistency for each threshold
    results = []
    ninety_percenters = []

    for stat, threshold in thresholds_config.items():
        if stat not in df.columns:
            print(f"Warning: {stat} not found in game log")
            continue

        result = calculate_consistency(df, stat, threshold, window_size)
        results.append(result)

        # Only show if meets minimum consistency threshold
        if result['consistency_pct'] >= min_consistency:
            ninety_percenters.append(result)

            # Print results
            print(f"⭐ {stat} >= {threshold}")
            print(f"  Consistency: {result['consistency_pct']:.1f}% ({result['hits']}/{result['total_games']} games)")
            print(f"  Average: {result['avg_value']:.1f}")
            print(f"  Range: {result['min_value']:.0f} - {result['max_value']:.0f}")
            print()

    # Summary
    if not ninety_percenters:
        print(f"No stats found with {min_consistency}%+ consistency")
    else:
        print(f"Found {len(ninety_percenters)} stat(s) with {min_consistency}%+ consistency!")

    return {
        'player': player['full_name'],
        'all_results': results,
        'ninety_percenters': ninety_percenters,
        'game_log': df
    }


def main():
    """Run proof of concept"""
    print("\n🏀 NBA 90%ers - Proof of Concept")
    print("="*60)

    # Example: Analyze a top scorer (you can change this)
    # Let's try LeBron James, Luka Doncic, or Giannis

    # Example 1: LeBron James
    print("\n📊 Example 1: LeBron James")
    analyze_player(
        player_name="LeBron James",
        thresholds_config={
            'PTS': 20,  # 20+ points
            'REB': 5,   # 5+ rebounds
            'AST': 5    # 5+ assists
        },
        window_size=20
    )

    # Example 2: Try another player
    print("\n" + "="*60)
    print("\n📊 Example 2: Luka Doncic")
    analyze_player(
        player_name="Luka Doncic",
        thresholds_config={
            'PTS': 25,  # 25+ points
            'REB': 7,   # 7+ rebounds
            'AST': 7    # 7+ assists
        },
        window_size=20
    )


if __name__ == "__main__":
    main()
