"""
Debug the date filtering
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

print(f"Before filtering: {len(df)} games")
print(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")

# Try the filtering
df['GAME_DATE_DT'] = pd.to_datetime(df['GAME_DATE'])
today = pd.Timestamp.now()

print(f"\nToday's date: {today}")
print(f"\nMost recent game date in data: {df['GAME_DATE_DT'].max()}")

# Filter
df_filtered = df[df['GAME_DATE_DT'] <= today].copy()

print(f"\nAfter filtering: {len(df_filtered)} games")

if len(df_filtered) > 0:
    print(f"\nActual games played (most recent 10):")
    print(df_filtered[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST']].head(10))
