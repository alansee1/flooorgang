"""
Let's figure out what data the NBA API is actually returning
"""

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd

# Find LeBron
all_players = players.get_players()
lebron = [p for p in all_players if 'lebron' in p['full_name'].lower()][0]

# Get game log
gamelog = playergamelog.PlayerGameLog(
    player_id=lebron['id'],
    season='2024-25',
    season_type_all_star='Regular Season'
)

df = gamelog.get_data_frames()[0]

print("Checking if this is real game data or projected data...")
print(f"\nTotal rows: {len(df)}")
print(f"\nAll columns: {df.columns.tolist()}")
print(f"\nFirst game (most recent):")
print(df.iloc[0])
print(f"\n\nLast game (earliest):")
print(df.iloc[-1])

# Check if there's a field indicating whether game was played
print("\n\nChecking WL (Win/Loss) field:")
print(df['WL'].value_counts())
print(f"\nAny null/empty WL values? {df['WL'].isna().sum()}")
