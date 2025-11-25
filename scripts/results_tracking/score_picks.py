#!/usr/bin/env python3
"""
Score picks by fetching actual game results from NBA and NFL APIs

Usage:
  python score_picks.py                    # Score yesterday's picks
  python score_picks.py 2025-11-13         # Score specific date
  python score_picks.py --unscored-only    # Only score unscored picks from yesterday
  python score_picks.py 2025-11-13 --unscored-only  # Only score unscored picks from specific date
"""

import sys
sys.path.append('src')

from database_v2 import get_supabase_client
from nba_api.stats.endpoints import playergamelog, leaguegamefinder
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
import time
import argparse

# NFL imports
try:
    import nflreadpy as nfl
    import polars as pl
    NFL_AVAILABLE = True
except ImportError:
    NFL_AVAILABLE = False
    print("⚠️  Warning: nflreadpy not available. NFL scoring will be skipped.")

# NFL stat type mappings (display name -> column name)
NFL_STAT_MAP = {
    'Pass Yds': 'passing_yards',
    'Rush Yds': 'rushing_yards',
    'Rec Yds': 'receiving_yards',
    'Receptions': 'receptions',
    'Pass TDs': 'passing_tds',
    'Completions': 'completions',
    'Attempts': 'attempts',
    'PTS': 'PTS'  # Team totals
}

# NFL team name to abbreviation mapping
NFL_TEAM_TO_ABBR = {
    'Arizona Cardinals': 'ARI',
    'Atlanta Falcons': 'ATL',
    'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR',
    'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN',
    'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET',
    'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU',
    'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAX',
    'Kansas City Chiefs': 'KC',
    'Las Vegas Raiders': 'LV',
    'Los Angeles Chargers': 'LAC',
    'Los Angeles Rams': 'LA',
    'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE',
    'New Orleans Saints': 'NO',
    'New York Giants': 'NYG',
    'New York Jets': 'NYJ',
    'Philadelphia Eagles': 'PHI',
    'Pittsburgh Steelers': 'PIT',
    'San Francisco 49ers': 'SF',
    'Seattle Seahawks': 'SEA',
    'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN',
    'Washington Commanders': 'WAS'
}

def get_player_id(player_name):
    """Get player ID from name (handles special characters)"""
    all_players = players.get_players()

    # Try exact match first
    player = [p for p in all_players if p['full_name'] == player_name]
    if player:
        return player[0]['id']

    # Try fuzzy match (remove accents/special chars)
    import unicodedata
    def normalize(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

    normalized_name = normalize(player_name)
    player = [p for p in all_players if normalize(p['full_name']) == normalized_name]
    return player[0]['id'] if player else None

def get_team_id(team_name):
    """Get team ID from name"""
    all_teams = teams.get_teams()
    team = [t for t in all_teams if t['full_name'] == team_name]
    return team[0]['id'] if team else None

def format_date_for_players(date_str):
    """Convert YYYY-MM-DD to 'MMM DD, YYYY' format for player API"""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return dt.strftime('%b %d, %Y')

def get_player_stats_for_date(player_name, date_str):
    """Fetch actual stats for a player on a specific date

    Args:
        player_name: Full player name
        date_str: Date in YYYY-MM-DD format
    """
    player_id = get_player_id(player_name)
    if not player_id:
        return None

    # Convert date format for player API (needs 'Nov 12, 2025')
    api_date = format_date_for_players(date_str)

    try:
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season='2025-26',
            season_type_all_star='Regular Season'
        )
        games = gamelog.get_data_frames()[0]

        # Find game on specified date
        game = games[games['GAME_DATE'] == api_date]

        if game.empty:
            return None

        return {
            'PTS': int(game.iloc[0]['PTS']),
            'REB': int(game.iloc[0]['REB']),
            'AST': int(game.iloc[0]['AST']),
            'FG3M': int(game.iloc[0]['FG3M'])
        }
    except:
        return None

def get_team_stats_for_date(team_name, date_str):
    """Fetch actual stats for a team on a specific date

    Args:
        team_name: Full team name
        date_str: Date in YYYY-MM-DD format
    """
    team_id = get_team_id(team_name)
    if not team_id:
        return None

    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id,
            season_nullable='2025-26',
            season_type_nullable='Regular Season'
        )
        games = gamefinder.get_data_frames()[0]

        # Find game on specified date (team API uses YYYY-MM-DD format)
        game = games[games['GAME_DATE'] == date_str]

        if game.empty:
            return None

        return {
            'PTS': int(game.iloc[0]['PTS'])
        }
    except Exception as e:
        print(f"  Error: {e}")
        return None


# NFL stat fetching functions
def get_nfl_player_stats_for_date(player_name, date_str):
    """Fetch actual NFL stats for a player on a specific date

    Args:
        player_name: Player's display name
        date_str: Date in YYYY-MM-DD format

    Returns:
        Dict with stat values or None if not found
    """
    if not NFL_AVAILABLE:
        return None

    try:
        # Load player stats for 2025 season
        player_stats = nfl.load_player_stats([2025])

        # Load schedules to map date to week
        schedules = nfl.load_schedules([2025])

        # Find the week for this date
        game = schedules.filter(pl.col('gameday') == date_str)
        if len(game) == 0:
            return None

        week = game.select('week').to_series().to_list()[0]

        # Find player's game for this week
        player_games = player_stats.filter(
            (pl.col('player_display_name') == player_name) &
            (pl.col('week') == week)
        )

        if len(player_games) == 0:
            return None

        # Extract stats
        game_row = player_games[0]

        return {
            'passing_yards': int(game_row['passing_yards'][0]) if game_row['passing_yards'][0] is not None else 0,
            'rushing_yards': int(game_row['rushing_yards'][0]) if game_row['rushing_yards'][0] is not None else 0,
            'receiving_yards': int(game_row['receiving_yards'][0]) if game_row['receiving_yards'][0] is not None else 0,
            'receptions': int(game_row['receptions'][0]) if game_row['receptions'][0] is not None else 0,
            'passing_tds': int(game_row['passing_tds'][0]) if game_row['passing_tds'][0] is not None else 0,
            'completions': int(game_row['completions'][0]) if game_row['completions'][0] is not None else 0,
            'attempts': int(game_row['attempts'][0]) if game_row['attempts'][0] is not None else 0
        }
    except Exception as e:
        print(f"  Error fetching NFL player stats: {e}")
        return None


def get_nfl_team_stats_for_date(team_abbr, date_str):
    """Fetch actual NFL team scoring for a specific date

    Args:
        team_abbr: Team abbreviation (e.g., 'BUF', 'HOU')
        date_str: Date in YYYY-MM-DD format

    Returns:
        Dict with team points or None if not found
    """
    if not NFL_AVAILABLE:
        return None

    try:
        # Load schedules
        schedules = nfl.load_schedules([2025])

        # Find game on this date where team played (home or away)
        game = schedules.filter(
            (pl.col('gameday') == date_str) &
            ((pl.col('home_team') == team_abbr) | (pl.col('away_team') == team_abbr))
        )

        if len(game) == 0:
            return None

        # Get the team's score
        game_row = game[0]
        if game_row['home_team'][0] == team_abbr:
            pts = int(game_row['home_score'][0])
        else:
            pts = int(game_row['away_score'][0])

        return {
            'PTS': pts
        }
    except Exception as e:
        print(f"  Error fetching NFL team stats: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Score NBA picks for a specific date')
    parser.add_argument('date', nargs='?', help='Date in YYYY-MM-DD format (default: yesterday)')
    parser.add_argument('--unscored-only', action='store_true',
                       help='Only score picks that have not been scored yet (result IS NULL)')
    args = parser.parse_args()

    # Default to yesterday if no date provided
    if args.date:
        scan_date = args.date
    else:
        yesterday = datetime.now() - timedelta(days=1)
        scan_date = yesterday.strftime('%Y-%m-%d')

    # Validate date format
    try:
        datetime.strptime(scan_date, '%Y-%m-%d')
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)

    print("\n" + "="*70)
    print(f"SCORING PICKS FOR {scan_date}")
    if args.unscored_only:
        print("(Unscored picks only)")
    print("="*70 + "\n")

    # Fetch picks from database
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Could not connect to database")
        return

    # Build query
    query = supabase.table('picks').select('*').eq('scan_date', scan_date)

    # Filter for unscored picks if requested
    if args.unscored_only:
        query = query.is_('result', 'null')

    result = query.execute()
    picks = result.data

    if not picks:
        if args.unscored_only:
            print(f"✅ No unscored picks found for {scan_date} (all picks already scored)")
        else:
            print(f"❌ No picks found for {scan_date}")
        return

    print(f"Found {len(picks)} picks to score\n")

    hit_count = 0
    miss_count = 0
    no_game_count = 0

    for pick in picks:
        entity_name = pick['entity_name']
        entity_type = pick['entity_type']
        stat_type = pick['stat_type']
        line = float(pick['line'])
        bet_type = pick['bet_type']
        sport = pick.get('sport', 'nba')  # Default to NBA for backwards compatibility

        print(f"Scoring [{sport.upper()}]: {entity_name} - {stat_type} {bet_type} {line}")

        # Fetch actual stats based on sport
        if sport == 'nba':
            if entity_type == 'player':
                stats = get_player_stats_for_date(entity_name, scan_date)
            else:
                stats = get_team_stats_for_date(entity_name, scan_date)
        elif sport == 'nfl':
            if entity_type == 'player':
                stats = get_nfl_player_stats_for_date(entity_name, scan_date)
            else:
                # For NFL teams, convert full name to abbreviation
                team_abbr = NFL_TEAM_TO_ABBR.get(entity_name, entity_name)
                stats = get_nfl_team_stats_for_date(team_abbr, scan_date)
        else:
            print(f"  ⚠️  Unknown sport: {sport}\n")
            no_game_count += 1
            continue

        if not stats:
            print(f"  ⚠️  No game found\n")
            no_game_count += 1
            continue

        # Get actual value for the stat type
        if sport == 'nfl':
            # Use the mapping to convert display name to column name
            stat_column = NFL_STAT_MAP.get(stat_type, stat_type.lower().replace(' ', '_'))
            actual = stats.get(stat_column)
        else:
            # NBA uses uppercase stat types
            actual = stats.get(stat_type)

        if actual is None:
            print(f"  ⚠️  Stat type '{stat_type}' not found in results\n")
            no_game_count += 1
            continue

        print(f"  Actual: {actual}")

        # Determine if hit
        if bet_type == 'OVER':
            hit = actual > line
        else:  # UNDER
            hit = actual < line

        print(f"  Result: {'✅ HIT' if hit else '❌ MISS'}\n")

        # Update database
        supabase.table('picks').update({
            'actual_value': actual,
            'result': 'hit' if hit else 'miss'
        }).eq('id', pick['id']).execute()

        if hit:
            hit_count += 1
        else:
            miss_count += 1

        time.sleep(0.6)  # Rate limit

    total = hit_count + miss_count
    hit_rate = (hit_count / total * 100) if total > 0 else 0

    print("="*70)
    print(f"FINAL RESULTS: {hit_count}/{total} HIT ({hit_rate:.1f}%)")
    if no_game_count > 0:
        print(f"Skipped: {no_game_count} picks (no game found)")
    print("="*70)

if __name__ == "__main__":
    main()
