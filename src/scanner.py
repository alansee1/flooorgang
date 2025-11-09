"""
League-Wide 90%ers Scanner
Analyzes all players with betting lines to find value opportunities
"""

from src.odds_fetcher import OddsFetcher
from src.player_stats import get_player_stats, calculate_90er_floors
from src.odds_cache import save_odds_to_cache, load_odds_from_cache, has_cache, get_cache_info
from src.player_stats_cache import save_player_stats, load_player_stats
from src.graphics_generator import create_value_picks_graphic
import numpy as np
import time
import sys


def analyze_all_players(player_props, delay=0.6, use_fresh_data=False):
    """
    Analyze all players with betting lines

    Args:
        player_props: Dict from OddsFetcher {player_name: {stat: line}}
        delay: Seconds between NBA API calls
        use_fresh_data: If True, skip cache and always fetch fresh stats

    Returns:
        Tuple of (opportunities list, games_data_map dict)
    """
    print("\n" + "="*60)
    print(f"Analyzing {len(player_props)} Players")
    print("="*60)

    all_opportunities = []
    players_analyzed = 0
    players_skipped = 0
    skip_reasons = {'no_games': 0, 'not_found': 0, 'error': 0}
    games_data_map = {}  # Store game data for graphics

    for i, (player_name, betting_lines) in enumerate(player_props.items(), 1):
        print(f"\n[{i}/{len(player_props)}] {player_name}")

        # Try to load from cache first (unless --fresh flag is set)
        cached_games = None if use_fresh_data else load_player_stats(player_name)

        if cached_games is not None:
            print(f"  📂 Using cached stats")
            player_data = {'player': player_name, 'games': cached_games}
        else:
            # Fetch from NBA API
            try:
                player_data = get_player_stats(player_name)

                if not player_data:
                    print(f"  ⚠️  Player not found in NBA API")
                    players_skipped += 1
                    skip_reasons['not_found'] += 1
                    continue

                if player_data['games'].empty:
                    print(f"  ⚠️  No games played this season")
                    players_skipped += 1
                    skip_reasons['no_games'] += 1
                    continue

                # Save to cache for next time
                save_player_stats(player_name, player_data['games'])

            except Exception as e:
                print(f"  ❌ Error fetching stats: {e}")
                players_skipped += 1
                skip_reasons['error'] += 1
                continue

            # Rate limit only when hitting API (not needed for cache)
            if i < len(player_props):
                time.sleep(delay)

        # Calculate 90%er floors for stats with betting lines
        stats_to_check = list(betting_lines.keys())

        try:
            floors = calculate_90er_floors(player_data['games'], stats_to_check)
        except Exception as e:
            print(f"  ❌ Error calculating floors: {e}")
            players_skipped += 1
            continue

        # Store game data for graphics
        games_data_map[player_name] = player_data['games']

        # Find value opportunities
        player_opps = find_value_opportunities(player_name, floors, betting_lines)

        if player_opps:
            print(f"  ✅ Found {len(player_opps)} value opportunity(ies)!")
            for opp in player_opps:
                print(f"     {opp['stat']}: {opp['confidence']} confidence")
            all_opportunities.extend(player_opps)
        else:
            print(f"  - No value found")

        players_analyzed += 1

    print(f"\n{'='*60}")
    print("SCAN COMPLETE")
    print(f"{'='*60}")
    print(f"Players analyzed: {players_analyzed}")
    print(f"Players skipped: {players_skipped}")
    if players_skipped > 0:
        print(f"\nSkip breakdown:")
        print(f"  - Player not found in NBA API: {skip_reasons['not_found']}")
        print(f"  - No games played this season: {skip_reasons['no_games']}")
        print(f"  - Other errors: {skip_reasons['error']}")
    print(f"\nTotal value opportunities: {len(all_opportunities)}")
    print(f"{'='*60}\n")

    return all_opportunities, games_data_map


def find_value_opportunities(player_name, floors, betting_lines):
    """
    Compare 90%er floors to betting lines to find value

    Args:
        player_name: Player's name
        floors: Dict of {stat: {floor, avg, min, max}}
        betting_lines: Dict of {stat: line}

    Returns:
        List of value opportunities
    """
    opportunities = []
    tolerance = 0.10  # 10%

    for stat, line in betting_lines.items():
        if stat not in floors:
            continue

        floor = floors[stat]['floor']

        # Calculate 10% range around the line
        lower_bound = line * (1 - tolerance)
        upper_bound = line * (1 + tolerance)

        # Check if floor is above lower bound (Over has value)
        if floor >= lower_bound:
            confidence = "HIGH" if floor >= line else "MEDIUM"

            opportunities.append({
                'player': player_name,
                'stat': stat,
                'line': line,
                'floor': floor,
                'avg': floors[stat]['avg'],
                'confidence': confidence,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            })

    return opportunities


def print_report(opportunities):
    """Print a nicely formatted report of all value opportunities"""

    if not opportunities:
        print("\n❌ No value opportunities found")
        print("Lines may be tight today, or floors are below ranges")
        return

    # Sort by confidence (HIGH first) then by player name
    opportunities.sort(key=lambda x: (x['confidence'] == 'MEDIUM', x['player']))

    print("\n" + "="*60)
    print("VALUE OPPORTUNITIES REPORT")
    print("="*60)

    # Group by confidence
    high_conf = [o for o in opportunities if o['confidence'] == 'HIGH']
    med_conf = [o for o in opportunities if o['confidence'] == 'MEDIUM']

    if high_conf:
        print(f"\n🔥 HIGH CONFIDENCE ({len(high_conf)} picks)")
        print("="*60)
        for opp in high_conf:
            print(f"\n{opp['player']}")
            print(f"  {opp['stat']}: Over {opp['line']}")
            print(f"  90%er Floor: {opp['floor']:.0f} (avg: {opp['avg']:.1f})")
            print(f"  ✅ Floor is AT OR ABOVE the line")

    if med_conf:
        print(f"\n⚡ MEDIUM CONFIDENCE ({len(med_conf)} picks)")
        print("="*60)
        for opp in med_conf:
            print(f"\n{opp['player']}")
            print(f"  {opp['stat']}: Over {opp['line']}")
            print(f"  90%er Floor: {opp['floor']:.0f} (avg: {opp['avg']:.1f})")
            print(f"  Range: {opp['lower_bound']:.1f} - {opp['upper_bound']:.1f}")
            print(f"  ✅ Floor is within 10% range")

    print(f"\n{'='*60}")
    print(f"TOTAL: {len(opportunities)} value opportunities")
    print(f"{'='*60}\n")


def main():
    """Run the full league-wide scanner"""
    print("\n🏀 NBA 90%ers - LEAGUE-WIDE SCANNER")
    print("="*60)
    print("Finding value opportunities across all games today")
    print("="*60)

    # Check for --fresh flag to bypass cache
    use_fresh_data = '--fresh' in sys.argv

    # Step 1: Get betting lines (from cache or API)
    player_props = None

    if not use_fresh_data and has_cache():
        print("\n📂 Cache found!")
        cache_info = get_cache_info()
        print(f"   Date: {cache_info['date']}")
        print(f"   Time: {cache_info['timestamp']}")
        print(f"   Players: {cache_info['player_count']}")

        response = input("\nUse cached odds? (y/n): ").lower().strip()

        if response == 'y':
            player_props = load_odds_from_cache()
        else:
            print("\nFetching fresh odds from API...")
    elif use_fresh_data and has_cache():
        print("\n🔄 --fresh flag set, skipping cache...")

    if player_props is None:
        # Fetch from API
        print("\nStep 1: Fetching betting lines from The Odds API...")
        try:
            fetcher = OddsFetcher()
            player_props = fetcher.get_all_player_props()

            if not player_props:
                print("\n❌ No player props available")
                return

            # Save to cache for next time
            save_odds_to_cache(player_props)

        except Exception as e:
            print(f"\n❌ Error fetching odds: {e}")
            return

    # Step 2: Analyze all players
    print("\nStep 2: Analyzing all players with props...")
    try:
        opportunities, games_data_map = analyze_all_players(player_props, use_fresh_data=use_fresh_data)
    except Exception as e:
        print(f"\n❌ Error during player analysis: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Print report
    print_report(opportunities)

    # Step 4: Generate graphic
    if opportunities:
        print("\nStep 3: Generating graphic...")
        graphic_path = create_value_picks_graphic(opportunities, games_data_map)
        if graphic_path:
            print(f"\n📸 Graphic ready to tweet!")
            print(f"   {graphic_path}")
    else:
        print("\n⚠️  No opportunities to visualize")


if __name__ == "__main__":
    main()
