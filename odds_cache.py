"""
Odds Cache Module
Save and load betting odds to avoid hitting API limits during development
"""

import json
import os
from datetime import datetime


CACHE_DIR = 'cache'
CACHE_FILE = os.path.join(CACHE_DIR, 'odds_cache.json')


def ensure_cache_dir():
    """Create cache directory if it doesn't exist"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def save_odds_to_cache(odds_data):
    """
    Save odds data to cache file

    Args:
        odds_data: Dict of {player_name: {stat: line}}
    """
    ensure_cache_dir()

    cache = {
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'player_count': len(odds_data),
        'data': odds_data
    }

    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

    print(f"💾 Saved odds to cache: {CACHE_FILE}")
    print(f"   Players: {len(odds_data)}")
    print(f"   Timestamp: {cache['timestamp']}")


def load_odds_from_cache():
    """
    Load odds data from cache file

    Returns:
        Dict of {player_name: {stat: line}} or None if no cache exists
    """
    if not os.path.exists(CACHE_FILE):
        return None

    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

    print(f"📂 Loaded odds from cache: {CACHE_FILE}")
    print(f"   Players: {cache.get('player_count', 'Unknown')}")
    print(f"   Cached on: {cache.get('timestamp', 'Unknown')}")

    return cache.get('data')


def has_cache():
    """Check if cache file exists"""
    return os.path.exists(CACHE_FILE)


def get_cache_info():
    """Get info about cached data without loading it"""
    if not has_cache():
        return None

    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

    return {
        'timestamp': cache.get('timestamp'),
        'date': cache.get('date'),
        'player_count': cache.get('player_count')
    }


def clear_cache():
    """Delete the cache file"""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print(f"🗑️  Cache cleared: {CACHE_FILE}")
    else:
        print("No cache to clear")
