"""
Database client for storing picks and scanner runs in Supabase
"""

import os
from datetime import datetime, date
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("⚠️  Warning: Supabase credentials not found in .env file")
    print("   Database storage will be skipped")
    supabase = None
else:
    supabase: Client = create_client(supabase_url, supabase_key)


def create_scanner_run(sport, scan_date, game_date=None):
    """
    Create a new scanner run record

    Args:
        sport: 'nba' or 'nfl'
        scan_date: Date when scan ran
        game_date: Date of first game (optional)

    Returns:
        run_id: ID of created run, or None if failed
    """
    if not supabase:
        return None

    try:
        result = supabase.table('scanner_runs').insert({
            'sport': sport,
            'scan_date': scan_date.isoformat() if isinstance(scan_date, date) else scan_date,
            'game_date': game_date.isoformat() if isinstance(game_date, date) else game_date,
            'total_picks': 0,
            'players_analyzed': 0,
            'players_skipped': 0
        }).execute()

        run_id = result.data[0]['id']
        print(f"✅ Created scanner run #{run_id}")
        return run_id

    except Exception as e:
        print(f"❌ Failed to create scanner run: {e}")
        return None


def update_scanner_run(run_id, **kwargs):
    """
    Update scanner run with stats

    Args:
        run_id: ID of run to update
        **kwargs: Fields to update (total_picks, players_analyzed, etc.)
    """
    if not supabase or not run_id:
        return

    try:
        supabase.table('scanner_runs').update(kwargs).eq('id', run_id).execute()
        print(f"✅ Updated scanner run #{run_id}")
    except Exception as e:
        print(f"❌ Failed to update scanner run: {e}")


def save_picks(run_id, picks, sport, scan_date, game_date=None, season='2025-26'):
    """
    Save picks to database

    Args:
        run_id: ID of scanner run
        picks: List of pick dictionaries from scanner
        sport: 'nba' or 'nfl'
        scan_date: Date when scan ran
        game_date: Date of game (optional)
        season: Season identifier

    Returns:
        Number of picks saved
    """
    if not supabase or not run_id or not picks:
        return 0

    # Transform picks to database format
    db_picks = []
    for pick in picks:
        db_pick = {
            'run_id': run_id,
            'sport': sport,
            'scan_date': scan_date.isoformat() if isinstance(scan_date, date) else scan_date,
            'game_date': game_date.isoformat() if isinstance(game_date, date) else game_date,
            'player_name': pick['player'],
            'stat_type': pick['stat'],
            'line': float(pick['line']),
            'floor': float(pick['floor']),
            'avg': float(pick['avg']),
            'confidence': pick.get('confidence', 'HIGH'),
            'bet_type': pick.get('bet_type', 'OVER'),
            'lower_bound': float(pick.get('lower_bound', 0)),
            'upper_bound': float(pick.get('upper_bound', 0)),
            'season': season
        }

        # Add ceiling if present (for team UNDER bets)
        if 'ceiling' in pick:
            db_pick['ceiling'] = float(pick['ceiling'])

        db_picks.append(db_pick)

    try:
        result = supabase.table('picks').insert(db_picks).execute()
        count = len(result.data)
        print(f"✅ Saved {count} picks to database")
        return count

    except Exception as e:
        print(f"❌ Failed to save picks: {e}")
        return 0


def save_scanner_results(sport, scan_date, picks, stats, game_date=None, api_requests_remaining=None, games_scheduled=None, games_with_props=None):
    """
    Convenience function to save complete scanner results

    Args:
        sport: 'nba' or 'nfl'
        scan_date: Date when scan ran
        picks: List of picks
        stats: Dict with 'analyzed', 'skipped' counts
        game_date: Date of first game (optional)
        api_requests_remaining: Remaining API quota from The Odds API (optional)
        games_scheduled: Total number of games scheduled (optional)
        games_with_props: Number of games with player props available (optional)

    Returns:
        run_id: ID of created run
    """
    # Create run
    run_id = create_scanner_run(sport, scan_date, game_date)

    if not run_id:
        return None

    # Save picks
    picks_saved = save_picks(run_id, picks, sport, scan_date, game_date)

    # Update run stats
    update_data = {
        'total_picks': picks_saved,
        'players_analyzed': stats.get('analyzed', 0),
        'players_skipped': stats.get('skipped', 0)
    }

    # Add API quota if available
    if api_requests_remaining is not None:
        update_data['api_requests_remaining'] = api_requests_remaining

    # Add games counts if available
    if games_scheduled is not None:
        update_data['games_scheduled'] = games_scheduled

    if games_with_props is not None:
        update_data['games_with_props'] = games_with_props

    update_scanner_run(run_id, **update_data)

    return run_id
