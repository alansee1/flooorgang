"""
Test NBA API for getting game schedule
"""

from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime, timedelta

print("\n🏀 Testing NBA Schedule API\n")

# Try today's scoreboard
print("Today's games:")
try:
    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()

    if games:
        for game in games:
            home = game.get('homeTeam', {}).get('teamTricode', 'UNK')
            away = game.get('awayTeam', {}).get('teamTricode', 'UNK')
            game_time = game.get('gameTimeUTC', 'Unknown')
            print(f"  {away} @ {home} - {game_time}")
    else:
        print("  No games today")

except Exception as e:
    print(f"  Error: {e}")

# Note: NBA API doesn't have a "next 7 days" endpoint
# We'd need to check each day individually or use a different approach
print("\nNote: NBA API Live only shows today's games")
print("For future days, we'd need to check day-by-day")
