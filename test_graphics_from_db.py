"""
Test graphics generation using picks from database
"""

from dotenv import load_dotenv
load_dotenv()

from src.database_v2 import supabase
from src.graphics_generator_v2 import create_picks_graphic


def fetch_latest_picks():
    """Fetch most recent picks from database"""
    if not supabase:
        print("❌ No Supabase connection")
        return []

    # Get latest scanner run
    result = supabase.table('scanner_runs').select('*').order('id', desc=True).limit(1).execute()

    if not result.data:
        print("❌ No scanner runs found")
        return []

    run_id = result.data[0]['id']
    print(f"✓ Found latest run: #{run_id}")

    # Fetch picks from that run
    picks_result = supabase.table('picks').select('*').eq('run_id', run_id).execute()

    if not picks_result.data:
        print("❌ No picks found for this run")
        return []

    print(f"✓ Found {len(picks_result.data)} picks")

    # Transform database picks to scanner format
    picks = []
    for db_pick in picks_result.data:
        if db_pick['entity_type'] == 'player':
            pick = {
                'player': db_pick['entity_name'],
                'team_abbr': db_pick['team_abbr'],
                'stat': db_pick['stat_type'],
                'floor': db_pick['floor'],
                'line': db_pick['line'],
                'odds': db_pick['odds'],
                'games': db_pick['games_analyzed'],
                'hit_rate': db_pick['hit_rate'],
                'game_history': db_pick.get('game_history', [])
            }
        else:  # team pick
            pick = {
                'team': db_pick['entity_name'],
                'team_abbr': db_pick['team_abbr'],
                'type': db_pick['bet_type'],
                'line': db_pick['line'],
                'odds': db_pick['odds'],
                'games': db_pick['games_analyzed'],
                'hit_rate': db_pick['hit_rate'],
                'game_history': db_pick.get('game_history', [])
            }

            # Add floor or ceiling based on bet type
            if db_pick['bet_type'] == 'OVER':
                pick['floor'] = db_pick['floor']
            else:
                pick['ceiling'] = db_pick['ceiling']

        picks.append(pick)

    return picks


def main():
    print("\n🎨 Testing Graphics from Database\n")

    # Fetch picks
    picks = fetch_latest_picks()

    if not picks:
        print("\n❌ No picks to display")
        return

    # Generate graphic
    print(f"\nGenerating graphic for {len(picks)} picks...")
    graphic_path = create_picks_graphic(picks, 'test_from_db.png')

    if graphic_path:
        print(f"\n✅ Success! Graphic saved to: {graphic_path}")
    else:
        print("\n❌ Failed to generate graphic")


if __name__ == "__main__":
    main()
