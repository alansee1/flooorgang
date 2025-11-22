"""
NFL Graphics Generator
Creates tweet-ready images for FlooorGang NFL picks (player + team)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import os


OUTPUT_DIR = 'graphics'


def ensure_output_dir():
    """Create graphics directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def create_nfl_picks_graphic(picks, output_filename=None, max_picks=10):
    """
    Create a mobile-optimized graphic showing top NFL picks

    Args:
        picks: List of picks from nfl_scanner (player + team picks)
        output_filename: Optional filename (defaults to date-based name)
        max_picks: Maximum number of picks to display (default 10)

    Returns:
        Path to saved image
    """
    ensure_output_dir()

    if not output_filename:
        date_str = datetime.now().strftime('%Y%m%d')
        output_filename = f"flooorgang_nfl_picks_{date_str}.png"

    filepath = os.path.join(OUTPUT_DIR, output_filename)

    if not picks:
        print("No picks to display")
        return None

    # Sort by best odds (descending, so -150 comes before -300)
    sorted_picks = sorted(picks, key=lambda p: p['odds'], reverse=True)[:max_picks]

    # Mobile-optimized: Square format (1080x1080) for better mobile viewing
    num_picks = len(sorted_picks)
    fig_width = 10.8  # 1080px at 100dpi
    fig_height = 10.8  # Square for mobile optimization

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='#0f1419')
    ax.set_facecolor('#0f1419')

    # Title - brand name and date
    date_str = datetime.now().strftime('%b %d')
    ax.text(0.5, 0.985, f'NFL @FlooorGang - {date_str}',
            ha='center', va='top', fontsize=24, fontweight='bold',
            color='white', transform=ax.transAxes)

    # Subtitle notes (single line with bullets) - more space below title
    subtitle_y = 0.945
    subtitle_text = "Odds from DraftKings  •  All 2025 season games analyzed  •  100% hit rate floors"
    ax.text(0.5, subtitle_y, subtitle_text,
            ha='center', va='top', fontsize=9,
            color='#888888', transform=ax.transAxes, style='italic')

    # Column Headers - more space below subtitle
    header_y = 0.90
    ax.text(0.02, header_y, 'ODDS', ha='left', va='center', fontsize=10,
            fontweight='bold', color='#888888', transform=ax.transAxes)
    ax.text(0.10, header_y, 'TEAM', ha='left', va='center', fontsize=10,
            fontweight='bold', color='#888888', transform=ax.transAxes)
    ax.text(0.18, header_y, 'PLAYER', ha='left', va='center', fontsize=10,
            fontweight='bold', color='#888888', transform=ax.transAxes)
    ax.text(0.38, header_y, 'BET', ha='left', va='center', fontsize=10,
            fontweight='bold', color='#888888', transform=ax.transAxes)
    ax.text(0.70, header_y, 'LAST 10 GAMES', ha='center', va='center', fontsize=10,
            fontweight='bold', color='#888888', transform=ax.transAxes)

    # Starting Y position - more space below headers
    y_start = 0.88
    # Dynamically calculate row height based on number of picks
    # Available space from y_start (0.85) to bottom margin (0.05) = 0.80
    available_space = 0.80
    row_height = available_space / num_picks if num_picks > 0 else 0.087

    # Draw each pick as a row
    for idx, pick in enumerate(sorted_picks):
        y_pos = y_start - (idx * row_height)
        draw_pick_row(ax, pick, y_pos, idx, row_height)

    # Remove axes
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Save with proper padding
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(filepath, dpi=100, bbox_inches=None, facecolor='#0f1419', pad_inches=0)
    plt.close()

    print(f"✅ Graphic saved: {filepath}")
    return filepath


def draw_pick_row(ax, pick, y_pos, row_idx, row_height):
    """
    Draw a single pick row

    Args:
        ax: Matplotlib axis
        pick: Pick dictionary (player or team)
        y_pos: Y position (0-1)
        row_idx: Row index for alternating colors
        row_height: Height of each row (dynamically calculated)
    """
    # Alternate row background for readability
    if row_idx % 2 == 0:
        bg_color = '#1a1f2e'
    else:
        bg_color = '#0f1419'

    # Background rectangle
    bg_rect = mpatches.Rectangle(
        (0, y_pos - row_height),
        1,
        row_height,
        facecolor=bg_color,
        edgecolor='none',
        transform=ax.transAxes
    )
    ax.add_patch(bg_rect)

    # Determine if player or team pick
    is_player = 'player' in pick

    if is_player:
        entity_name = pick['player']
        stat = pick['stat']
        bet_type = 'OVER'
        reference = pick['floor']
    else:
        entity_name = pick['team']
        stat = 'PTS'
        bet_type = pick['type']
        reference = pick.get('floor') if bet_type == 'OVER' else pick.get('ceiling')

    line = pick['line']
    odds = pick['odds']
    team_abbr = pick.get('team_abbr', '???')
    hit_rate = pick['hit_rate']
    games = pick['games']
    game_history = pick.get('game_history', [])

    # Text positioning
    text_y = y_pos - (row_height / 2)

    # Column 1: Odds (moved to left)
    odds_color = '#ffaa00' if odds > -300 else '#888888'
    ax.text(0.02, text_y, f"{odds:+d}",
            ha='left', va='center', fontsize=12, fontweight='bold',
            color=odds_color, transform=ax.transAxes)

    # Column 2: Team abbreviation (use NFL team abbreviations)
    # For NFL, we need to get the team abbreviation from the pick
    if is_player:
        # For player picks, we need to map team name to abbreviation
        # This should come from the pick data
        display_abbr = team_abbr if team_abbr != '???' else 'NFL'
    else:
        # For team picks, extract abbreviation from team name
        team_parts = entity_name.split()
        if len(team_parts) > 2:
            # Multi-word team names (e.g., "New England Patriots" -> "NE")
            display_abbr = get_nfl_team_abbr(entity_name)
        else:
            display_abbr = get_nfl_team_abbr(entity_name)

    ax.text(0.10, text_y, display_abbr,
            ha='left', va='center', fontsize=13, fontweight='bold',
            color='#ff6600', transform=ax.transAxes)  # Orange for NFL

    # Column 3: Player/Team name (smart formatting)
    if is_player:
        # For players: abbreviate first name if too long
        if len(entity_name) > 16:
            parts = entity_name.split()
            if len(parts) >= 2:
                name_display = f"{parts[0][0]}. {' '.join(parts[1:])}"
            else:
                name_display = entity_name[:13] + '...'
        else:
            name_display = entity_name
    else:
        # For teams: show just the team name (drop city)
        team_parts = entity_name.split()
        if len(team_parts) > 1:
            name_display = team_parts[-1]  # Just the last word (team name)
        else:
            name_display = entity_name

    ax.text(0.18, text_y, name_display,
            ha='left', va='center', fontsize=12,
            color='white', transform=ax.transAxes)

    # Column 4: Stat + Line + Bet Type
    pick_text = f"{stat} {line} {bet_type}"
    ax.text(0.38, text_y, pick_text,
            ha='left', va='center', fontsize=11, fontweight='bold',
            color='#00ff88', transform=ax.transAxes)

    # Column 5: Game History Checkboxes with values inside
    if game_history and len(game_history) > 0:
        # Show up to 10 most recent games
        recent_games = game_history[:10]
        checkbox_start_x = 0.55
        checkbox_spacing = 0.043
        checkbox_size = 0.035

        for game_idx, value in enumerate(recent_games):
            checkbox_x = checkbox_start_x + (game_idx * checkbox_spacing)

            # All boxes are green since we have 100% hit rate
            checkbox_color = '#00ff88'
            checkbox = mpatches.Rectangle(
                (checkbox_x, text_y - checkbox_size/2),
                checkbox_size,
                checkbox_size,
                facecolor=checkbox_color,
                edgecolor='white',
                linewidth=1,
                transform=ax.transAxes
            )
            ax.add_patch(checkbox)

            # Add value inside checkbox (dark text on green background)
            ax.text(checkbox_x + checkbox_size/2, text_y, f"{int(value)}",
                    ha='center', va='center', fontsize=9,
                    color='#0f1419', fontweight='bold',
                    transform=ax.transAxes)


def get_nfl_team_abbr(team_name):
    """Get NFL team abbreviation from full team name"""
    abbr_map = {
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
    return abbr_map.get(team_name, 'NFL')


def main():
    """Test the NFL graphics generator"""
    print("\n🎨 Testing NFL Graphics Generator\n")

    # Mock picks for testing
    test_picks = [
        {
            'player': 'Patrick Mahomes',
            'team_abbr': 'KC',
            'stat': 'Pass Yds',
            'floor': 250,
            'line': 245.5,
            'odds': -226,
            'games': 10,
            'hit_rate': '10/10',
            'game_history': [280, 265, 290, 310, 255, 275, 300, 268, 285, 292]
        },
        {
            'player': 'Josh Allen',
            'team_abbr': 'BUF',
            'stat': 'Pass TDs',
            'floor': 2,
            'line': 1.5,
            'odds': -306,
            'games': 9,
            'hit_rate': '9/9',
            'game_history': [3, 2, 4, 2, 3, 2, 3, 2, 2]
        },
        {
            'team': 'Buffalo Bills',
            'team_abbr': 'BUF',
            'type': 'OVER',
            'floor': 20,
            'line': 18.5,
            'odds': -352,
            'games': 9,
            'hit_rate': '9/9',
            'game_history': [24, 27, 30, 23, 28, 31, 26, 29, 25]
        }
    ]

    filepath = create_nfl_picks_graphic(test_picks, 'test_nfl_picks.png')
    print(f"\n✓ Test graphic created at: {filepath}")


if __name__ == "__main__":
    main()
