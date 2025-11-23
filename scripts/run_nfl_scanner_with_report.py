#!/usr/bin/env python3
"""
NFL Scanner wrapper that runs scanner and sends detailed Slack report
"""

import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Add src to path
sys.path.append('src')

from nfl_scanner import NFLScanner
from notifier import notify_scanner_success, notify_scanner_error
from nfl_odds_fetcher import NFLOddsFetcher
from twitter_poster import TwitterPoster


def main():
    try:
        print(f"Starting NFL scanner at {datetime.now()}")

        # Run scanner (with DB saving and graphics generation enabled)
        scanner = NFLScanner(odds_threshold=-500, season=2025, save_to_db=True, create_graphic=True)
        picks = scanner.scan()

        # Get first game time
        fetcher = NFLOddsFetcher()
        games = fetcher.get_todays_games()
        first_game_time = None
        if games:
            earliest_game = min(games, key=lambda g: g['commence_time'])
            game_time = datetime.fromisoformat(earliest_game['commence_time'].replace('Z', '+00:00'))
            pst = ZoneInfo("America/Los_Angeles")
            game_time_pst = game_time.astimezone(pst)
            first_game_time = f"{earliest_game['home_team']} vs {earliest_game['away_team']} at {game_time_pst.strftime('%I:%M %p %Z')}"

        # Determine graphic path
        graphic_path = f"graphics/flooorgang_nfl_picks_{datetime.now().strftime('%Y%m%d')}.png" if picks else None

        # Post to Twitter
        if picks:
            print(f"\n🐦 Posting to Twitter...")
            try:
                twitter = TwitterPoster()

                # Build tweet text for NFL
                date_str = datetime.now().strftime('%b %d')
                num_picks = len(picks)

                tweet_text = f"🏈 NFL Picks - {date_str}\n\n"
                tweet_text += f"{num_picks} plays identified\n\n"

                # Sort by best odds (descending, matching graphic sort)
                sorted_picks = sorted(picks, key=lambda p: p['odds'], reverse=True)

                # Add top 3 picks as text
                for i, pick in enumerate(sorted_picks[:3], 1):
                    if 'player' in pick:
                        entity = pick['player']
                        stat = pick['stat']
                        line = pick['line']
                        tweet_text += f"{i}. {entity} {stat} O{line}\n"
                    else:
                        entity = pick['team']
                        # Shorten team names
                        team_parts = entity.split()
                        if len(team_parts) > 2:
                            entity = " ".join(team_parts[1:])
                        bet_type = pick['type']
                        line = pick['line']
                        symbol = 'O' if bet_type == 'OVER' else 'U'
                        tweet_text += f"{i}. {entity} {symbol}{line}\n"

                tweet_text += f"\nFull card below 👇"

                # Post tweet with graphic (note: post_with_image handles printing success/URL)
                tweet_id = twitter.post_with_image(tweet_text, graphic_path)

                if not tweet_id:
                    print(f"⚠️  Twitter post failed (check logs)")

            except Exception as e:
                print(f"⚠️  Twitter post failed: {e}")

        # Send success notification
        notify_scanner_success(
            num_picks=len(picks) if picks else 0,
            top_picks=picks[:4] if picks else None,
            first_game_time=first_game_time,
            graphic_path=graphic_path
        )

        print(f"\nNFL Scanner completed successfully at {datetime.now()}")
        print(f"✅ Generated {len(picks) if picks else 0} picks")

    except Exception as e:
        print(f"❌ NFL Scanner failed: {e}")

        # Send error notification
        import traceback
        tb = traceback.format_exc()
        notify_scanner_error(str(e), tb)

        sys.exit(1)


if __name__ == "__main__":
    main()
