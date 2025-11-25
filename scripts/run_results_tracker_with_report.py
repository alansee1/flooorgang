#!/usr/bin/env python3
"""
Results tracker wrapper that scores picks and sends detailed Slack report
"""

import sys
import os
from datetime import datetime, timedelta
import argparse

# Add src to path
sys.path.append('src')

from database_v2 import get_supabase_client
from notifier import notify_results_tracker_success, notify_results_tracker_error

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


def score_picks(scan_date, unscored_only=False):
    """
    Score picks for given date and return stats
    Returns: (hit_count, miss_count, total, best_pick, worst_pick)
    """
    # Import scoring functions from score_picks
    sys.path.append('scripts/results_tracking')
    from score_picks import (
        get_player_stats_for_date, get_team_stats_for_date,
        get_nfl_player_stats_for_date, get_nfl_team_stats_for_date
    )
    import time

    supabase = get_supabase_client()

    # Build query
    query = supabase.table('picks').select('*').eq('scan_date', scan_date)

    # Filter for unscored picks if requested
    if unscored_only:
        query = query.is_('result', 'null')

    result = query.execute()
    picks = result.data

    if not picks:
        return None, None, 0, None, None

    print(f"Found {len(picks)} picks to score\n")

    hit_count = 0
    miss_count = 0
    best_pick = None
    worst_pick = None
    max_margin = 0
    min_margin = float('inf')

    for pick in picks:
        entity_name = pick['entity_name']
        entity_type = pick['entity_type']
        stat_type = pick['stat_type']
        line = float(pick['line'])
        # OVER bets have floor, UNDER bets have ceiling
        floor = float(pick['floor']) if pick.get('floor') is not None else None
        ceiling = float(pick['ceiling']) if pick.get('ceiling') is not None else None
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
            continue

        if not stats:
            print(f"  ⚠️  No game found\n")
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
            continue

        print(f"  Actual: {actual}")

        # Determine if hit
        if bet_type == 'OVER':
            hit = actual > line
            margin = actual - line
        else:  # UNDER
            hit = actual < line
            margin = line - actual

        print(f"  Result: {'✅ HIT' if hit else '❌ MISS'}\n")

        # Update database
        supabase.table('picks').update({
            'actual_value': actual,
            'result': 'hit' if hit else 'miss'
        }).eq('id', pick['id']).execute()

        # Track best/worst
        if hit and margin > max_margin:
            max_margin = margin
            best_pick = {
                'entity': entity_name,
                'stat': stat_type,
                'line': line,
                'actual': actual,
                'type': bet_type
            }

        if not hit and margin < min_margin:
            min_margin = margin
            worst_pick = {
                'entity': entity_name,
                'stat': stat_type,
                'line': line,
                'actual': actual,
                'floor': floor if bet_type == 'OVER' else ceiling,
                'type': bet_type
            }

        if hit:
            hit_count += 1
        else:
            miss_count += 1

        time.sleep(0.6)  # Rate limit

    total = hit_count + miss_count

    return hit_count, miss_count, total, best_pick, worst_pick


def main():
    parser = argparse.ArgumentParser(description='Score picks and send Slack report')
    parser.add_argument('date', nargs='?', help='Date to score (YYYY-MM-DD), defaults to yesterday')
    parser.add_argument('--unscored-only', action='store_true', help='Only score picks that haven\'t been scored yet')
    args = parser.parse_args()

    # Determine date
    if args.date:
        scan_date = args.date
    else:
        yesterday = datetime.now() - timedelta(days=1)
        scan_date = yesterday.strftime('%Y-%m-%d')

    try:
        print(f"Starting results tracker for {scan_date} at {datetime.now()}")

        # Score picks
        hit_count, miss_count, total, best_pick, worst_pick = score_picks(scan_date, args.unscored_only)

        if total == 0 or total is None:
            print(f"✅ No picks to score for {scan_date}")
            # Don't send notification if no picks (normal for unscored-only mode)
            return

        hit_rate = (hit_count / total * 100) if total > 0 else 0

        print("="*70)
        print(f"FINAL RESULTS: {hit_count}/{total} HIT ({hit_rate:.1f}%)")
        print("="*70)

        # Send success notification
        notify_results_tracker_success(
            date=scan_date,
            num_scored=total,
            hit_count=hit_count,
            miss_count=miss_count,
            hit_rate=hit_rate,
            best_pick=best_pick,
            worst_pick=worst_pick
        )

        print(f"Results tracker completed successfully at {datetime.now()}")

    except Exception as e:
        print(f"❌ Results tracker failed: {e}")

        # Send error notification
        import traceback
        tb = traceback.format_exc()
        notify_results_tracker_error(str(e), tb)

        sys.exit(1)


if __name__ == "__main__":
    main()
