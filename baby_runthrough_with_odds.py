"""
Baby Run-Through with REAL Betting Odds
Full workflow: Player stats → 90%er floors → Real odds → Value detection
"""

from baby_runthrough import get_player_stats, calculate_90er_floors, compare_to_betting_lines
from odds_fetcher import OddsFetcher
import time


def main():
    """Run baby example with REAL betting odds"""
    print("\n🏀 NBA 90%ers - Baby Run-Through with REAL ODDS")
    print("="*60)

    # Step 1: Fetch real betting lines
    print("\nStep 1: Fetching real betting lines from The Odds API...")
    try:
        fetcher = OddsFetcher()
        all_props = fetcher.get_all_player_props()

        if not all_props:
            print("\n❌ No player props available. Try again later when lines are posted.")
            return

        print(f"\n✅ Got betting lines for {len(all_props)} players")

    except Exception as e:
        print(f"\n❌ Error fetching odds: {e}")
        return

    # Step 2: Pick a player who has props available
    # Let's try to find Giannis or another star
    test_players = [
        "Giannis Antetokounmpo",
        "Shai Gilgeous-Alexander",
        "Luka Doncic",
        "Anthony Davis",
        "Nikola Jokic"
    ]

    selected_player = None
    for player_name in test_players:
        if player_name in all_props:
            selected_player = player_name
            break

    if not selected_player:
        # Just pick the first player with multiple props
        for player, props in all_props.items():
            if len(props) >= 2:  # Has at least 2 stat lines
                selected_player = player
                break

    if not selected_player:
        print("\n❌ No suitable player found with betting lines")
        return

    print(f"\n{'='*60}")
    print(f"Selected Player: {selected_player}")
    print(f"{'='*60}")

    betting_lines = all_props[selected_player]
    print(f"\nBetting lines available:")
    for stat, line in betting_lines.items():
        print(f"  {stat}: {line}")

    # Step 3: Get player's season stats
    print(f"\n{'='*60}")
    print(f"Step 2: Fetching {selected_player}'s season stats...")
    print(f"{'='*60}")

    time.sleep(0.6)  # NBA API rate limit

    player_data = get_player_stats(selected_player)

    if not player_data:
        print(f"\n❌ Could not fetch stats for {selected_player}")
        return

    # Step 4: Calculate 90%er floors
    stats_to_check = list(betting_lines.keys())  # Only check stats we have lines for
    floors = calculate_90er_floors(player_data['games'], stats_to_check)

    # Step 5: Compare and find value
    value_opps = compare_to_betting_lines(floors, betting_lines)

    # Step 6: Summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"\nPlayer: {selected_player}")
    print(f"Games Played: {len(player_data['games'])}")

    if value_opps:
        print(f"\n✅ Found {len(value_opps)} value opportunity(ies):\n")
        for opp in value_opps:
            print(f"  🎯 {opp['stat']}: Over {opp['line']}")
            print(f"     Confidence: {opp['confidence']}")
            print(f"     90%er Floor: {opp['floor']:.0f}")
            print(f"     Valid Range: {opp['range']}")
            print()
    else:
        print("\n❌ No value opportunities found")
        print("This player's 90%er floors are below the betting ranges")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
