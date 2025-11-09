"""
Test with more current players to verify real data
"""

from poc_player_stats import analyze_player

print("🏀 Testing with Top NBA Players - 2025-26 Season\n")

# Test multiple stars
players_to_test = [
    ("Giannis Antetokounmpo", {'PTS': 25, 'REB': 10}),
    ("Anthony Davis", {'PTS': 20, 'REB': 10}),
    ("Jayson Tatum", {'PTS': 25, 'REB': 7}),
]

for player_name, thresholds in players_to_test:
    analyze_player(player_name, thresholds, window_size=20)
    print("\n" + "="*60 + "\n")
