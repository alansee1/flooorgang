#!/usr/bin/env python3
"""
Score picks from 11/12 by fetching actual game results
Uses existing codebase modules
"""

import sys
sys.path.append('src')

from database_v2 import get_supabase_client
from nba_api.stats.endpoints import playergamelog, leaguegamefinder
from nba_api.stats.static import players, teams
from datetime import datetime
import time

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

def get_player_stats_for_date(player_name, date_str='Nov 12, 2025'):
    """Fetch actual stats for a player on a specific date"""
    player_id = get_player_id(player_name)
    if not player_id:
        return None

    try:
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season='2025-26',
            season_type_all_star='Regular Season'
        )
        games = gamelog.get_data_frames()[0]

        # Find game on 11/12
        game = games[games['GAME_DATE'] == date_str]

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

def get_team_stats_for_date(team_name, date_str='2025-11-12'):
    """Fetch actual stats for a team on a specific date"""
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

        # Find game on 11/12
        game = games[games['GAME_DATE'] == date_str]

        if game.empty:
            return None

        return {
            'PTS': int(game.iloc[0]['PTS'])
        }
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("\n" + "="*70)
    print("SCORING 11/12 PICKS")
    print("="*70 + "\n")

    # Fetch picks from database
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Could not connect to database")
        return

    result = supabase.table('picks').select('*').eq('scan_date', '2025-11-12').execute()
    picks = result.data

    print(f"Found {len(picks)} picks to score\n")

    hit_count = 0
    miss_count = 0

    for pick in picks:
        entity_name = pick['entity_name']
        entity_type = pick['entity_type']
        stat_type = pick['stat_type']
        line = float(pick['line'])
        bet_type = pick['bet_type']

        print(f"Scoring: {entity_name} - {stat_type} {bet_type} {line}")

        # Fetch actual stats
        if entity_type == 'player':
            stats = get_player_stats_for_date(entity_name)
        else:
            stats = get_team_stats_for_date(entity_name)

        if not stats:
            print(f"  ⚠️  No game found\n")
            continue

        actual = stats[stat_type]
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
    print("="*70)

if __name__ == "__main__":
    main()
