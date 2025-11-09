"""
Scan multiple players to find 90%ers
"""

from poc_player_stats import analyze_player

print("\n🏀 Searching for 90%ers - 2025-26 Season")
print("="*60)

# List of top players to scan
players_to_check = [
    # Player name, thresholds to check
    ("Giannis Antetokounmpo", {'PTS': 25, 'PTS_30': 30, 'REB': 10, 'REB_12': 12}),
    ("Luka Doncic", {'PTS': 25, 'PTS_30': 30, 'REB': 7, 'AST': 7}),
    ("Anthony Davis", {'PTS': 20, 'REB': 10, 'BLK': 2}),
    ("Nikola Jokic", {'PTS': 20, 'REB': 10, 'AST': 7}),
    ("Stephen Curry", {'PTS': 20, 'PTS_25': 25, 'FG3M': 3}),
    ("Kevin Durant", {'PTS': 25, 'PTS_30': 30}),
    ("Joel Embiid", {'PTS': 25, 'REB': 10}),
    ("Jayson Tatum", {'PTS': 25, 'REB': 7}),
    ("Shai Gilgeous-Alexander", {'PTS': 25, 'PTS_30': 30}),
    ("Damian Lillard", {'PTS': 20, 'AST': 6}),
]

print("\nScanning players for 90%+ consistency...\n")

found_any = False

for player_name, thresholds in players_to_check:
    result = analyze_player(player_name, thresholds, window_size=20, min_consistency=90.0)

    # Track if we found any 90%ers
    if result and result.get('ninety_percenters'):
        found_any = True

    print()

if not found_any:
    print("\n" + "="*60)
    print("No 90%ers found yet - season is still early!")
    print("Try lowering threshold to 80% or waiting for more games")
