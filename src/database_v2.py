"""
Database v2 - Multi-sport support with team abbreviations
Stores picks and scanner runs in Supabase for NBA and NFL
"""

import os
from datetime import datetime, date
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Supabase credentials (loaded once, client created on demand)
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
_supabase_client = None

def get_supabase_client() -> Optional[Client]:
    """Lazy-load Supabase client to avoid import-time initialization issues"""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not supabase_url or not supabase_key:
        print("⚠️  Warning: Supabase credentials not found")
        print("   Database storage will be skipped")
        return None

    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except Exception as e:
        print(f"⚠️  Warning: Failed to create Supabase client: {e}")
        return None


# NBA Team Abbreviations
NBA_TEAM_ABBR = {
    'Atlanta Hawks': 'ATL',
    'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA',
    'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL',
    'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU',
    'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC',
    'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA',
    'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS',
}

# NFL Team Abbreviations
NFL_TEAM_ABBR = {
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


def get_team_abbr(team_name: str, sport: str = 'nba') -> Optional[str]:
    """
    Get team abbreviation from full team name

    Args:
        team_name: Full team name
        sport: 'nba' or 'nfl'

    Returns:
        Team abbreviation or None if not found
    """
    if sport == 'nba':
        return NBA_TEAM_ABBR.get(team_name)
    elif sport == 'nfl':
        return NFL_TEAM_ABBR.get(team_name)
    return None


def create_scanner_run(sport: str, scan_date: date, game_date: Optional[date] = None) -> Optional[int]:
    """
    Create a new scanner run record

    Args:
        sport: 'nba' or 'nfl'
        scan_date: Date when scan ran
        game_date: Date of first game (optional)

    Returns:
        run_id: ID of created run, or None if failed
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        result = supabase.table('scanner_runs').insert({
            'sport': sport,
            'scan_date': scan_date.isoformat() if isinstance(scan_date, date) else scan_date,
            'game_date': game_date.isoformat() if isinstance(game_date, date) else game_date,
            'total_picks': 0,
            'player_picks': 0,
            'team_picks': 0,
            'entities_analyzed': 0,
            'entities_skipped': 0
        }).execute()

        run_id = result.data[0]['id']
        print(f"✅ Created scanner run #{run_id}")
        return run_id

    except Exception as e:
        print(f"❌ Failed to create scanner run: {e}")
        return None


def update_scanner_run(run_id: int, **kwargs):
    """
    Update scanner run with stats

    Args:
        run_id: ID of run to update
        **kwargs: Fields to update (total_picks, entities_analyzed, etc.)
    """
    supabase = get_supabase_client()
    if not supabase or not run_id:
        return

    try:
        supabase.table('scanner_runs').update(kwargs).eq('id', run_id).execute()
        print(f"✅ Updated scanner run #{run_id}")
    except Exception as e:
        print(f"❌ Failed to update scanner run: {e}")


def save_picks(
    run_id: int,
    picks: List[Dict],
    sport: str,
    scan_date: date,
    game_date: Optional[date] = None,
    season: str = '2025-26'
) -> int:
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
    supabase = get_supabase_client()
    if not supabase or not run_id or not picks:
        return 0

    # Transform picks to database format
    db_picks = []
    for pick in picks:
        # Determine entity type and name
        if 'player' in pick:
            entity_type = 'player'
            entity_name = pick['player']
            stat_type = pick['stat']
            bet_type = 'OVER'
            floor = float(pick['floor'])
            ceiling = None
            # Use team_abbr from pick if available (from NBA API), otherwise try lookup
            team_abbr = pick.get('team_abbr') or get_team_abbr(entity_name, sport)
            # Get game history (array of values)
            game_history = pick.get('game_history', [])
        else:  # team pick
            entity_type = 'team'
            entity_name = pick['team']
            stat_type = 'PTS'  # Team totals are always points
            bet_type = pick['type']
            floor = float(pick.get('floor', 0)) if 'floor' in pick else None
            ceiling = float(pick.get('ceiling', 0)) if 'ceiling' in pick else None
            # Get team abbreviation from team name
            team_abbr = get_team_abbr(entity_name, sport)
            # Get team game history (points from recent games)
            game_history = pick.get('game_history', [])

        db_pick = {
            'run_id': run_id,
            'sport': sport,
            'scan_date': scan_date.isoformat() if isinstance(scan_date, date) else scan_date,
            'game_date': game_date.isoformat() if isinstance(game_date, date) else game_date,
            'entity_type': entity_type,
            'entity_name': entity_name,
            'team_abbr': team_abbr,
            'stat_type': stat_type,
            'bet_type': bet_type,
            'line': float(pick['line']),
            'odds': int(pick['odds']),
            'floor': floor,
            'ceiling': ceiling,
            'games_analyzed': int(pick['games']),
            'hit_rate': pick['hit_rate'],
            'game_history': game_history,
            'season': season
        }

        db_picks.append(db_pick)

    try:
        result = supabase.table('picks').insert(db_picks).execute()
        count = len(result.data)
        print(f"✅ Saved {count} picks to database")
        return count

    except Exception as e:
        print(f"❌ Failed to save picks: {e}")
        return 0


def save_scanner_results(
    sport: str,
    scan_date: date,
    picks: List[Dict],
    stats: Dict,
    game_date: Optional[date] = None,
    api_requests_remaining: Optional[int] = None,
    season: str = '2025-26'
) -> Optional[int]:
    """
    Convenience function to save complete scanner results

    Args:
        sport: 'nba' or 'nfl'
        scan_date: Date when scan ran
        picks: List of picks
        stats: Dict with 'analyzed', 'skipped', 'player_picks', 'team_picks' counts
        game_date: Date of first game (optional)
        api_requests_remaining: Remaining API quota from The Odds API (optional)
        season: Season identifier

    Returns:
        run_id: ID of created run
    """
    # Create run
    run_id = create_scanner_run(sport, scan_date, game_date)

    if not run_id:
        return None

    # Save picks
    picks_saved = save_picks(run_id, picks, sport, scan_date, game_date, season)

    # Count player vs team picks
    player_picks = len([p for p in picks if 'player' in p])
    team_picks = len([p for p in picks if 'team' in p])

    # Update run stats
    update_data = {
        'total_picks': picks_saved,
        'player_picks': player_picks,
        'team_picks': team_picks,
        'entities_analyzed': stats.get('analyzed', 0),
        'entities_skipped': stats.get('skipped', 0)
    }

    # Add API quota if available
    if api_requests_remaining is not None:
        update_data['api_requests_remaining'] = api_requests_remaining

    update_scanner_run(run_id, **update_data)

    return run_id


def main():
    """Test the database v2"""
    print("\n🗄️  Testing Database v2\n")

    # Test team abbreviation lookup
    print("Testing team abbreviation lookup:")
    test_teams = ['New York Knicks', 'Denver Nuggets', 'Memphis Grizzlies']
    for team in test_teams:
        abbr = get_team_abbr(team)
        print(f"  {team} → {abbr}")

    print("\n✓ Database v2 module loaded successfully")


if __name__ == "__main__":
    main()
