"""
Quick check to see what data we're actually pulling
"""

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd

# Find LeBron
all_players = players.get_players()
lebron = [p for p in all_players if 'lebron' in p['full_name'].lower()][0]

print(f"Player: {lebron['full_name']}")
print(f"Player ID: {lebron['id']}\n")

# Get game log for 2024-25 season
gamelog = playergamelog.PlayerGameLog(
    player_id=lebron['id'],
    season='2024-25',
    season_type_all_star='Regular Season'
)

df = gamelog.get_data_frames()[0]

print(f"Total games returned: {len(df)}")
print(f"\nFirst 5 games (most recent):")
print(df[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST']].head(10))
print(f"\nDate range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
print(f"\nSeason ID in data: {df['SEASON_ID'].unique()}")
