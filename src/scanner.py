"""
League-Wide 90%ers Scanner
Analyzes all players with betting lines to find value opportunities
"""

from src.odds_fetcher import OddsFetcher
from src.player_stats import get_player_stats, calculate_90er_floors
from src.team_stats import get_team_stats, calculate_team_floors_ceilings
from src.odds_cache import save_odds_to_cache, load_odds_from_cache, has_cache, get_cache_info
from src.player_stats_cache import save_player_stats, load_player_stats
from src.graphics_generator import create_value_picks_graphic
from src.database import save_scanner_results
from src.twitter_poster import TwitterPoster
import numpy as np
import time
import sys
from datetime import date


def analyze_all_players(player_props, delay=0.6, use_fresh_data=False):
    """
    Analyze all players with betting lines

    Args:
        player_props: Dict from OddsFetcher {player_name: {stat: line}}
        delay: Seconds between NBA API calls
        use_fresh_data: If True, skip cache and always fetch fresh stats

    Returns:
        Tuple of (opportunities list, games_data_map dict, stats dict)
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

        # Check minimum games requirement (6 games)
        num_games = len(player_data['games'])
        if num_games < 6:
            print(f"  ⚠️  Only {num_games} games played (minimum 6 required)")
            players_skipped += 1
            skip_reasons['no_games'] += 1
            continue

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

    stats = {
        'analyzed': players_analyzed,
        'skipped': players_skipped
    }

    return all_opportunities, games_data_map, stats


def analyze_all_teams(team_totals, delay=0.6):
    """
    Analyze all teams with betting lines for team totals

    Args:
        team_totals: Dict from OddsFetcher {team_name: line}
        delay: Seconds between NBA API calls

    Returns:
        List of team opportunities (OVER and UNDER bets)
    """
    print("\n" + "="*60)
    print(f"Analyzing {len(team_totals)} Teams")
    print("="*60)

    team_opportunities = []
    teams_analyzed = 0
    teams_skipped = 0

    for i, (team_name, line) in enumerate(team_totals.items(), 1):
        print(f"\n[{i}/{len(team_totals)}] {team_name}")

        # Fetch team stats from NBA API
        try:
            team_data = get_team_stats(team_name)

            if not team_data:
                print(f"  ⚠️  Team not found in NBA API")
                teams_skipped += 1
                continue

            if team_data['games'].empty:
                print(f"  ⚠️  No games played this season")
                teams_skipped += 1
                continue

        except Exception as e:
            print(f"  ❌ Error fetching stats: {e}")
            teams_skipped += 1
            continue

        # Calculate floor (min) and ceiling (max) for team points
        try:
            stats = calculate_team_floors_ceilings(team_data['games'])

            if not stats:
                print(f"  ❌ Error calculating stats")
                teams_skipped += 1
                continue

        except Exception as e:
            print(f"  ❌ Error calculating stats: {e}")
            teams_skipped += 1
            continue

        # Find value opportunities (OVER and UNDER)
        team_opps = find_team_value_opportunities(team_name, stats, line)

        if team_opps:
            print(f"  ✅ Found {len(team_opps)} value opportunity(ies)!")
            for opp in team_opps:
                print(f"     {opp['bet_type']}: {opp['confidence']} confidence")
            team_opportunities.extend(team_opps)
        else:
            print(f"  - No value found")

        teams_analyzed += 1

        # Rate limit between API calls
        if i < len(team_totals):
            time.sleep(delay)

    print(f"\n{'='*60}")
    print("TEAM ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Teams analyzed: {teams_analyzed}")
    print(f"Teams skipped: {teams_skipped}")
    print(f"Total team opportunities: {len(team_opportunities)}")
    print(f"{'='*60}\n")

    return team_opportunities


def find_team_value_opportunities(team_name, stats, line):
    """
    Compare team floor/ceiling to betting line to find value
    Returns picks where:
    - OVER: floor >= line * 0.9
    - UNDER: ceiling <= line * 1.1

    Args:
        team_name: Team's name
        stats: Dict with floor, ceiling, avg, etc.
        line: Betting line for team total

    Returns:
        List of value opportunities (can include both OVER and UNDER)
    """
    opportunities = []
    tolerance = 0.10  # 10%

    floor = stats['floor']
    ceiling = stats['ceiling']

    # Calculate 10% range around the line
    lower_bound = line * (1 - tolerance)
    upper_bound = line * (1 + tolerance)

    # Check OVER value (floor within 10% below line)
    if floor >= lower_bound:
        opportunities.append({
            'team': team_name,
            'player': team_name,  # For database compatibility
            'stat': 'PTS',
            'line': line,
            'floor': floor,
            'ceiling': ceiling,
            'avg': stats['avg'],
            'confidence': 'HIGH',
            'bet_type': 'OVER',
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        })

    # Check UNDER value (ceiling within 10% above line)
    if ceiling <= upper_bound:
        opportunities.append({
            'team': team_name,
            'player': team_name,  # For database compatibility
            'stat': 'PTS',
            'line': line,
            'floor': floor,
            'ceiling': ceiling,
            'avg': stats['avg'],
            'confidence': 'HIGH',
            'bet_type': 'UNDER',
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        })

    return opportunities


def find_value_opportunities(player_name, floors, betting_lines):
    """
    Compare floors to betting lines to find value
    Returns picks where floor is within 10% of the betting line

    Args:
        player_name: Player's name
        floors: Dict of {stat: {floor, avg, min, max}}
        betting_lines: Dict of {stat: line}

    Returns:
        List of value opportunities where floor >= lower_bound (line * 0.9)
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

        # Include picks where floor is within 10% of the line
        if floor >= lower_bound:
            opportunities.append({
                'player': player_name,
                'stat': stat,
                'line': line,
                'floor': floor,
                'avg': floors[stat]['avg'],
                'confidence': 'HIGH',  # Single tier - all picks are HIGH
                'bet_type': 'OVER',  # Player props are always OVER bets
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
            # Check if this is a team pick (has 'team' field) or player pick
            is_team = 'team' in opp and opp.get('team') == opp.get('player')
            bet_type = opp.get('bet_type', 'OVER')

            print(f"\n{opp['player']}")
            print(f"  {opp['stat']}: {bet_type} {opp['line']}")

            if is_team:
                # Team pick - show floor or ceiling based on bet type
                if bet_type == 'OVER':
                    print(f"  Team Floor: {opp['floor']:.0f} (avg: {opp['avg']:.1f})")
                else:  # UNDER
                    print(f"  Team Ceiling: {opp['ceiling']:.0f} (avg: {opp['avg']:.1f})")
            else:
                # Player pick
                print(f"  90%er Floor: {opp['floor']:.0f} (avg: {opp['avg']:.1f})")

            print(f"  ✅ Floor is AT OR ABOVE the line")

    if med_conf:
        print(f"\n⚡ MEDIUM CONFIDENCE ({len(med_conf)} picks)")
        print("="*60)
        for opp in med_conf:
            is_team = 'team' in opp and opp.get('team') == opp.get('player')
            bet_type = opp.get('bet_type', 'OVER')

            print(f"\n{opp['player']}")
            print(f"  {opp['stat']}: {bet_type} {opp['line']}")

            if is_team:
                if bet_type == 'OVER':
                    print(f"  Team Floor: {opp['floor']:.0f} (avg: {opp['avg']:.1f})")
                else:
                    print(f"  Team Ceiling: {opp['ceiling']:.0f} (avg: {opp['avg']:.1f})")
            else:
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

    # Track API requests remaining and games count
    api_requests_remaining = None
    games_scheduled = None
    games_with_props = None

    if player_props is None:
        # Fetch from API
        print("\nStep 1: Fetching betting lines from The Odds API...")
        try:
            fetcher = OddsFetcher()
            player_props = fetcher.get_all_player_props()

            if not player_props:
                print("\n❌ No player props available")
                return

            # Capture API quota and games count
            api_requests_remaining = fetcher.requests_remaining
            if api_requests_remaining and api_requests_remaining != 'Unknown':
                api_requests_remaining = int(api_requests_remaining)

            games_scheduled = fetcher.games_scheduled
            games_with_props = fetcher.games_with_props

            # Save to cache for next time
            save_odds_to_cache(player_props)

        except Exception as e:
            print(f"\n❌ Error fetching odds: {e}")
            return

    # Step 2: Fetch team totals
    team_totals = None
    print("\nStep 2: Fetching team totals from The Odds API...")
    try:
        if player_props is not None:
            # Reuse same fetcher if available
            if 'fetcher' not in locals():
                fetcher = OddsFetcher()
            team_totals = fetcher.get_all_team_totals()
        else:
            print("⚠️  Skipping team totals (no player props)")
    except Exception as e:
        print(f"⚠️  Error fetching team totals: {e}")
        team_totals = {}

    # Step 3: Analyze all players
    print("\nStep 3: Analyzing all players with props...")
    try:
        opportunities, games_data_map, stats = analyze_all_players(player_props, use_fresh_data=use_fresh_data)
    except Exception as e:
        print(f"\n❌ Error during player analysis: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Analyze all teams
    if team_totals:
        print("\nStep 4: Analyzing all teams with totals...")
        try:
            team_opportunities = analyze_all_teams(team_totals)
            # Merge team opportunities with player opportunities
            opportunities.extend(team_opportunities)
        except Exception as e:
            print(f"\n❌ Error during team analysis: {e}")
            import traceback
            traceback.print_exc()

    # Step 5: Print report
    print_report(opportunities)

    # Step 6: Save to database
    if opportunities:
        print("\nStep 6: Saving picks to database...")
        try:
            run_id = save_scanner_results(
                sport='nba',
                scan_date=date.today(),
                picks=opportunities,
                stats=stats,
                game_date=None,  # Could extract from games_data_map if needed
                api_requests_remaining=api_requests_remaining,
                games_scheduled=games_scheduled,
                games_with_props=games_with_props
            )
            if run_id:
                print(f"✅ Saved to database (run #{run_id})")
                if api_requests_remaining:
                    print(f"📊 API quota remaining: {api_requests_remaining}")
                if games_scheduled and games_with_props:
                    print(f"🏀 Games: {games_with_props}/{games_scheduled} had props")
        except Exception as e:
            print(f"⚠️  Database save failed (continuing anyway): {e}")

    # Step 7: Generate graphic
    if opportunities:
        print("\nStep 7: Generating graphic...")
        graphic_path = create_value_picks_graphic(opportunities, games_data_map)
        if graphic_path:
            print(f"\n📸 Graphic generated: {graphic_path}")

            # Step 8: Post to Twitter (if --tweet flag is set)
            if '--tweet' in sys.argv:
                print("\n🐦 Posting to Twitter...")
                try:
                    poster = TwitterPoster()

                    # Generate tweet text
                    num_picks = len(opportunities)
                    tweet_text = f"🏀 {num_picks} high-confidence picks for today\n\nFloor stats = 90th percentile over last 10 games\n\n#NBA #PropBets #SportsBetting"

                    # Post tweet with graphic
                    tweet_id = poster.post_with_image(tweet_text, graphic_path)

                    if tweet_id:
                        print(f"✅ Posted to @FlooorGang!")
                    else:
                        print(f"❌ Failed to post to Twitter")

                except Exception as e:
                    print(f"⚠️  Twitter posting failed: {e}")
            else:
                print("💡 Add --tweet flag to auto-post to Twitter")
    else:
        print("\n⚠️  No opportunities to visualize")


if __name__ == "__main__":
    main()
