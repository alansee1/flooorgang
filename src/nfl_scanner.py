"""
NFL Scanner - 100%er Finder
Scans NFL games for betting opportunities where lines are below player/team floors
"""

from dotenv import load_dotenv
load_dotenv()

from nfl_odds_fetcher import NFLOddsFetcher
from nfl_stats_analyzer import NFLStatsAnalyzer
from database_v2 import save_scanner_results
from datetime import date
from typing import List, Dict


# Team abbreviation mappings
TEAM_ABBR_MAP = {
    'Arizona Cardinals': 'ARI',
    'Atlanta Falcons': 'ATL',
    'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR',
    'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN',
    'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET',
    'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU',
    'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAX',
    'Kansas City Chiefs': 'KC',
    'Las Vegas Raiders': 'LV',
    'Los Angeles Chargers': 'LAC',
    'Los Angeles Rams': 'LAR',
    'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE',
    'New Orleans Saints': 'NO',
    'New York Giants': 'NYG',
    'New York Jets': 'NYJ',
    'Philadelphia Eagles': 'PHI',
    'Pittsburgh Steelers': 'PIT',
    'San Francisco 49ers': 'SF',
    'Seattle Seahawks': 'SEA',
    'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN',
    'Washington Commanders': 'WAS'
}


class NFLScanner:
    """Scans NFL games for 100%er opportunities"""

    def __init__(self, odds_threshold: int = -500, season: int = 2025):
        """
        Args:
            odds_threshold: Skip picks with odds worse than this (default -500)
            season: NFL season year (default 2025)
        """
        self.odds_threshold = odds_threshold
        self.season = season
        self.odds_fetcher = NFLOddsFetcher()
        self.stats_analyzer = NFLStatsAnalyzer(season=season)

    def scan(self) -> List[Dict]:
        """
        Scan today's NFL games for 100%er opportunities

        Returns:
            List of pick dictionaries ready for database
        """
        print("=" * 80)
        print("NFL 100%ER SCANNER")
        print("=" * 80)

        # Get today's games
        print("\nFetching today's NFL games...")
        games = self.odds_fetcher.get_todays_games()

        if not games:
            print("✓ No NFL games today")
            return []

        print(f"✓ Found {len(games)} game(s) today\n")

        all_picks = []

        for game in games:
            print(f"{'=' * 80}")
            print(f"Scanning: {game['away_team']} @ {game['home_team']}")
            print(f"{'=' * 80}\n")

            # Scan player props
            player_picks = self._scan_player_props(game['id'])
            all_picks.extend(player_picks)

            # Scan team totals
            team_picks = self._scan_team_totals(game['id'], game['home_team'], game['away_team'])
            all_picks.extend(team_picks)

        # Summary
        print(f"\n{'=' * 80}")
        print("SCAN COMPLETE")
        print(f"{'=' * 80}")
        print(f"Total 100%er opportunities found: {len(all_picks)}")

        if all_picks:
            print("\nPicks:")
            for i, pick in enumerate(all_picks, 1):
                if 'player' in pick:
                    print(f"  {i}. {pick['player']} {pick['stat']} O{pick['line']} @ {pick['odds']}")
                else:
                    print(f"  {i}. {pick['team']} {pick['type']} {pick['line']} @ {pick['odds']}")

        return all_picks

    def _scan_player_props(self, game_id: str) -> List[Dict]:
        """Scan player props for a game"""
        print("Scanning player props...")

        # Get all player lines
        player_props = self.odds_fetcher.get_player_props(game_id)

        if not player_props:
            print("  No player props found")
            return []

        print(f"  Found props for {len(player_props)} players")

        picks = []

        for player_name, stats in player_props.items():
            for stat_display, lines in stats.items():
                # Get stat column name
                stat_column = NFLOddsFetcher.STAT_COLUMNS.get(stat_display)
                if not stat_column:
                    continue

                # Get player's floor
                floor_data = self.stats_analyzer.get_player_floor(player_name, stat_column)
                if not floor_data:
                    continue

                floor = floor_data['floor']

                # Find lines below floor
                lines_below = [l for l in lines if l['line'] < floor]

                if lines_below:
                    # Get best line (highest below floor, with odds filter)
                    best_line = max(lines_below, key=lambda x: x['line'])

                    if best_line['odds'] > self.odds_threshold:
                        edge = floor - best_line['line']

                        picks.append({
                            'player': player_name,
                            'stat': stat_display,
                            'floor': floor,
                            'line': best_line['line'],
                            'odds': best_line['odds'],
                            'games': floor_data['games'],
                            'hit_rate': f"{floor_data['games']}/{floor_data['games']}",
                            'game_history': floor_data['history']
                        })

                        print(f"  ✅ {player_name} {stat_display} O{best_line['line']} @ {best_line['odds']}")

        if not picks:
            print("  No player prop opportunities found")

        return picks

    def _scan_team_totals(self, game_id: str, home_team: str, away_team: str) -> List[Dict]:
        """Scan team totals for a game"""
        print("\nScanning team totals...")

        # Get team total lines
        team_totals = self.odds_fetcher.get_team_totals(game_id)

        if not team_totals:
            print("  No team totals found")
            return []

        print(f"  Found totals for {len(team_totals)} teams")

        picks = []

        for team_name, lines in team_totals.items():
            # Get team abbreviation
            team_abbr = TEAM_ABBR_MAP.get(team_name)
            if not team_abbr:
                continue

            # Get team's floor and ceiling
            team_data = self.stats_analyzer.get_team_floor_ceiling(team_abbr)
            if not team_data:
                continue

            floor = team_data['floor']
            ceiling = team_data['ceiling']

            # Check OVER opportunities (lines below floor)
            overs = sorted(lines['overs'], key=lambda x: x['line'])
            overs_below_floor = [l for l in overs if l['line'] < floor]

            if overs_below_floor:
                best_over = max(overs_below_floor, key=lambda x: x['line'])
                if best_over['odds'] > self.odds_threshold:
                    picks.append({
                        'team': team_name,
                        'type': 'OVER',
                        'floor': floor,
                        'line': best_over['line'],
                        'odds': best_over['odds'],
                        'games': team_data['games'],
                        'hit_rate': f"{team_data['games']}/{team_data['games']}",
                        'game_history': team_data['history']
                    })
                    print(f"  ✅ {team_name} OVER {best_over['line']} @ {best_over['odds']}")

            # Check UNDER opportunities (lines above ceiling)
            unders = sorted(lines['unders'], key=lambda x: x['line'], reverse=True)
            unders_above_ceiling = [l for l in unders if l['line'] > ceiling]

            if unders_above_ceiling:
                best_under = min(unders_above_ceiling, key=lambda x: x['line'])
                if best_under['odds'] > self.odds_threshold:
                    picks.append({
                        'team': team_name,
                        'type': 'UNDER',
                        'ceiling': ceiling,
                        'line': best_under['line'],
                        'odds': best_under['odds'],
                        'games': team_data['games'],
                        'hit_rate': f"{team_data['games']}/{team_data['games']}",
                        'game_history': team_data['history']
                    })
                    print(f"  ✅ {team_name} UNDER {best_under['line']} @ {best_under['odds']}")

        if not picks:
            print("  No team total opportunities found")

        return picks


def main():
    """Run the scanner and save results"""
    scanner = NFLScanner(odds_threshold=-500, season=2025)

    # Scan for picks
    picks = scanner.scan()

    if picks:
        # Save to database
        print(f"\nSaving {len(picks)} pick(s) to database...")

        scan_date = date.today()
        game_date = scan_date  # For NFL, game date = scan date (we scan day-of)

        stats = {
            'analyzed': len(set([p.get('player') or p.get('team') for p in picks])),
            'skipped': 0
        }

        save_scanner_results(
            sport='nfl',
            scan_date=scan_date,
            picks=picks,
            stats=stats,
            game_date=game_date,
            api_requests_remaining=scanner.odds_fetcher.requests_remaining,
            season='2025-26'  # NFL season spans two calendar years
        )

        print("✅ Scanner completed successfully!")
    else:
        print("\n❌ No picks found")


if __name__ == "__main__":
    main()
