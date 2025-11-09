"""
Player Stats Cache Module
Cache NBA player game logs to speed up repeated runs
"""

import json
import os
from datetime import datetime
import pandas as pd


CACHE_DIR = 'cache'
PLAYER_STATS_FILE = os.path.join(CACHE_DIR, 'player_stats_cache.json')


def ensure_cache_dir():
    """Create cache directory if it doesn't exist"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def save_player_stats(player_name, games_df):
    """
    Save player's game stats to cache

    Args:
        player_name: Player's name
        games_df: DataFrame of game logs
    """
    ensure_cache_dir()

    # Load existing cache
    cache = {}
    if os.path.exists(PLAYER_STATS_FILE):
        with open(PLAYER_STATS_FILE, 'r') as f:
            cache = json.load(f)

    # Convert DataFrame to dict for JSON storage
    # Convert any Timestamp columns to strings first
    games_dict = games_df.copy()
    for col in games_dict.columns:
        if games_dict[col].dtype == 'datetime64[ns]':
            games_dict[col] = games_dict[col].astype(str)

    cache[player_name] = {
        'timestamp': datetime.now().isoformat(),
        'games': games_dict.to_dict('records')  # List of game dicts
    }

    # Save back
    with open(PLAYER_STATS_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def load_player_stats(player_name):
    """
    Load player's game stats from cache

    Args:
        player_name: Player's name

    Returns:
        DataFrame of games or None if not cached/expired
    """
    if not os.path.exists(PLAYER_STATS_FILE):
        return None

    try:
        with open(PLAYER_STATS_FILE, 'r') as f:
            cache = json.load(f)
    except json.JSONDecodeError:
        # Cache is corrupted, delete it
        print(f"  ⚠️  Cache corrupted, rebuilding...")
        os.remove(PLAYER_STATS_FILE)
        return None

    if player_name not in cache:
        return None

    player_data = cache[player_name]

    # Check if cache is from today (refresh daily)
    cached_date = datetime.fromisoformat(player_data['timestamp']).date()
    today = datetime.now().date()

    if cached_date < today:
        # Cache is old, return None to trigger refresh
        return None

    # Convert back to DataFrame
    games_df = pd.DataFrame(player_data['games'])

    # Convert date strings back to datetime if needed
    if 'GAME_DATE_DT' in games_df.columns:
        games_df['GAME_DATE_DT'] = pd.to_datetime(games_df['GAME_DATE_DT'])

    return games_df


def clear_player_cache():
    """Delete the player stats cache"""
    if os.path.exists(PLAYER_STATS_FILE):
        os.remove(PLAYER_STATS_FILE)
        print(f"🗑️  Player stats cache cleared")
    else:
        print("No player cache to clear")
