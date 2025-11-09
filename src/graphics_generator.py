"""
Graphics Generator
Creates tweet-ready images for NBA 90%ers picks
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


def create_value_picks_graphic(opportunities, games_data_map=None, output_filename=None):
    """
    Create a mobile-optimized graphic showing game-by-game checkbox history

    Args:
        opportunities: List of value opportunities from scanner
        games_data_map: Dict of {player_name: games_df} to show game history
        output_filename: Optional filename (defaults to date-based name)

    Returns:
        Path to saved image
    """
    ensure_output_dir()

    if not output_filename:
        date_str = datetime.now().strftime('%Y%m%d')
        output_filename = f"90ers_picks_{date_str}.png"

    filepath = os.path.join(OUTPUT_DIR, output_filename)

    # Smart pick selection: All HIGH confidence + fill with MEDIUM up to 10 total
    high_conf = [o for o in opportunities if o['confidence'] == 'HIGH']
    med_conf = [o for o in opportunities if o['confidence'] == 'MEDIUM']

    # Combine and sort by player name (so same player's picks are together)
    all_picks = high_conf + med_conf
    all_picks.sort(key=lambda x: (x['player'], x['stat']))  # Sort by player name, then stat

    # Take top 10
    picks = all_picks[:10]

    if not picks:
        print("No picks to display")
        return None

    # Mobile-optimized: Square format (1080x1080) for better mobile viewing
    # Dynamically size based on number of picks
    num_picks = len(picks)
    fig_width = 10.8  # 1080px at 100dpi
    fig_height = 10.8  # Square for mobile optimization

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='#0f1419')
    ax.set_facecolor('#0f1419')

    # Title - brand name and date
    date_str = datetime.now().strftime('%b %d')
    ax.text(0.5, 0.985, f'@FlooorGang - {date_str}',
            ha='center', va='top', fontsize=24, fontweight='bold',
            color='white', transform=ax.transAxes)

    # Starting Y position - proper spacing from title
    y_start = 0.88
    row_height = 0.135  # Fixed height per row

    # Draw each pick as a row
    for idx, pick in enumerate(picks):
        y_pos = y_start - (idx * row_height)

        # Get game history AND actual values
        game_history = None
        game_values = None
        if games_data_map and pick['player'] in games_data_map:
            games_df = games_data_map[pick['player']]
            stat = pick['stat']
            threshold = pick['floor']

            # Get last 20 games (or all available)
            # MUST sort by GAME_DATE descending to ensure most recent first
            if 'GAME_DATE_DT' in games_df.columns:
                last_games = games_df.sort_values('GAME_DATE_DT', ascending=False).head(20)
            else:
                # Fallback to GAME_DATE if GAME_DATE_DT doesn't exist
                last_games = games_df.sort_values('GAME_DATE', ascending=False).head(20)

            game_values = last_games[stat].values  # Actual stat values
            game_history = game_values >= threshold  # Boolean array (hit/miss)

        draw_pick_row(ax, pick, y_pos, game_history, game_values, idx)

    # Remove axes
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Save with proper padding (no tight bbox which crops incorrectly)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(filepath, dpi=100, bbox_inches=None, facecolor='#0f1419', pad_inches=0)
    plt.close()

    print(f"✅ Graphic saved: {filepath}")
    return filepath


def draw_pick_row(ax, pick, y_pos, game_history, game_values, row_idx):
    """
    Draw a single pick row with checkbox game history

    Args:
        ax: Matplotlib axis
        pick: Pick dictionary
        y_pos: Y position (0-1)
        game_history: Boolean array of last 10 games (True = hit, False = miss)
        game_values: Actual stat values for each game
        row_idx: Row index for alternating colors
    """
    # Alternate row background for readability
    if row_idx % 2 == 0:
        bg_color = '#1a1f2e'
    else:
        bg_color = '#0f1419'

    # Background - no spacing between rows
    bg_height = 0.135
    bg = mpatches.Rectangle(
        (0.02, y_pos - 0.070), 0.96, bg_height,
        facecolor=bg_color,
        edgecolor='#2a2f3e',
        linewidth=0.5,
        transform=ax.transAxes
    )
    ax.add_patch(bg)

    # Left side: Player | Stat | Floor
    stat_map = {'PTS': 'PTS', 'REB': 'REB', 'AST': 'AST', 'FG3M': '3PM'}
    stat_abbr = stat_map.get(pick['stat'], pick['stat'])

    # Use full name
    full_name = pick['player']

    label_text = f"{full_name} | {stat_abbr} {pick['floor']:.0f}+"
    # Center text vertically in the row
    ax.text(0.04, y_pos,
            label_text,
            fontsize=15, fontweight='bold', color='white',
            va='center', transform=ax.transAxes)

    # Right side: Checkbox grid with VALUES inside (centered with text)
    if game_history is not None and len(game_history) > 0:
        draw_checkbox_grid(ax, game_history, game_values, y_pos, start_x_override=0.48)
    else:
        # No game data available
        ax.text(0.96, y_pos, 'No data',
                fontsize=10, color='#8899a6', ha='right', va='center',
                transform=ax.transAxes)


def draw_checkbox_grid(ax, game_history, game_values, y_pos, start_x_override=None):
    """
    Draw checkbox grid showing hit/miss with actual stat values inside

    Args:
        ax: Matplotlib axis
        game_history: Boolean array (True = hit, False = miss)
        game_values: Actual stat values for each game
        y_pos: Y position
        start_x_override: Optional fixed start position instead of right-aligned
    """
    num_games = len(game_history)  # Show all games
    box_size = 0.038  # Optimized for square format
    spacing = 0.043   # Tighter spacing for square layout

    if start_x_override:
        start_x = start_x_override
    else:
        start_x = 0.95 - (num_games * spacing)  # Right-aligned

    # Data is already sorted descending (most recent first)
    # Display left to right: most recent → oldest
    for i, (hit, value) in enumerate(zip(game_history, game_values)):
        x_pos = start_x + (i * spacing)

        # Color based on hit/miss
        if hit:
            color = '#22c55e'  # Green
            text_color = 'white'
        else:
            color = '#ef4444'  # Red
            text_color = 'white'

        # Draw checkbox centered vertically with text
        box = mpatches.Rectangle(
            (x_pos, y_pos - box_size/2), box_size, box_size,
            facecolor=color,
            edgecolor='white',
            linewidth=1.5,
            transform=ax.transAxes
        )
        ax.add_patch(box)

        # Add value text inside box centered
        ax.text(x_pos + box_size/2, y_pos,
                f'{int(value)}',
                fontsize=9, fontweight='bold', color=text_color,
                ha='center', va='center',
                transform=ax.transAxes)


def create_player_detail_graphic(player_name, floors, betting_lines, games_df, output_filename=None):
    """
    Create a detailed graphic for a single player showing their game history

    Args:
        player_name: Player's name
        floors: Dict of {stat: {floor, avg, min, max}}
        betting_lines: Dict of {stat: line}
        games_df: DataFrame of player's games
        output_filename: Optional filename

    Returns:
        Path to saved image
    """
    ensure_output_dir()

    if not output_filename:
        safe_name = player_name.replace(' ', '_')
        date_str = datetime.now().strftime('%Y%m%d')
        output_filename = f"player_{safe_name}_{date_str}.png"

    filepath = os.path.join(OUTPUT_DIR, output_filename)

    # Create figure with subplots for each stat
    num_stats = len(betting_lines)
    fig, axes = plt.subplots(num_stats, 1, figsize=(12, 3 * num_stats),
                             facecolor='#0f1419')

    if num_stats == 1:
        axes = [axes]

    fig.suptitle(f'{player_name} - Last 10 Games',
                 fontsize=20, fontweight='bold', color='white', y=0.98)

    stat_map = {
        'PTS': 'Points',
        'REB': 'Rebounds',
        'AST': 'Assists',
        'FG3M': '3-Pointers Made'
    }

    for idx, (stat, line) in enumerate(betting_lines.items()):
        ax = axes[idx]
        ax.set_facecolor('#0f1419')

        if stat not in floors:
            continue

        floor_val = floors[stat]['floor']

        # Get last 10 games for this stat
        games_data = games_df.sort_values('GAME_DATE', ascending=False)
        last_10 = games_data[stat].head(10).values[::-1]  # Reverse for chronological order

        # Create bar chart
        x_pos = range(len(last_10))
        colors = ['#4ade80' if val >= floor_val else '#f87171' for val in last_10]

        bars = ax.bar(x_pos, last_10, color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)

        # Add horizontal lines
        ax.axhline(y=line, color='#ffd93d', linestyle='--', linewidth=2,
                   label=f'Betting Line: {line}')
        ax.axhline(y=floor_val, color='#60a5fa', linestyle='-', linewidth=2,
                   label=f'90%er Floor: {floor_val:.0f}')

        # Labels and formatting
        stat_name = stat_map.get(stat, stat)
        ax.set_title(stat_name, fontsize=16, fontweight='bold', color='white', pad=10)
        ax.set_xlabel('Game (chronological)', fontsize=11, color='#8899a6')
        ax.set_ylabel('Value', fontsize=11, color='#8899a6')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([f'G{i+1}' for i in x_pos], color='#8899a6')
        ax.tick_params(colors='#8899a6')

        # Spine colors
        for spine in ax.spines.values():
            spine.set_color('#8899a6')

        # Legend
        ax.legend(loc='upper left', framealpha=0.9, facecolor='#1a1f2e',
                 edgecolor='#8899a6', labelcolor='white')

        # Grid
        ax.grid(axis='y', alpha=0.2, color='#8899a6')

    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='#0f1419')
    plt.close()

    print(f"✅ Player detail graphic saved: {filepath}")
    return filepath


def main():
    """Test graphics generation with mock data"""
    print("\n🎨 Testing Graphics Generator")
    import pandas as pd
    import numpy as np

    # Mock data
    mock_opportunities = [
        {
            'player': 'Giannis Antetokounmpo',
            'stat': 'PTS',
            'line': 30.5,
            'floor': 30,
            'avg': 33.4,
            'confidence': 'HIGH'
        },
        {
            'player': 'Nikola Jokic',
            'stat': 'AST',
            'line': 7.5,
            'floor': 9,
            'avg': 11.9,
            'confidence': 'HIGH'
        },
        {
            'player': 'Shai Gilgeous-Alexander',
            'stat': 'PTS',
            'line': 30.5,
            'floor': 30,
            'avg': 33.0,
            'confidence': 'MEDIUM'
        },
        {
            'player': 'Anthony Davis',
            'stat': 'REB',
            'line': 10.5,
            'floor': 10,
            'avg': 11.2,
            'confidence': 'MEDIUM'
        }
    ]

    # Mock game data with realistic hit/miss patterns
    mock_games = {
        'Giannis Antetokounmpo': pd.DataFrame({
            'GAME_DATE': pd.date_range('2025-10-30', periods=10, freq='2D'),
            'PTS': [32, 30, 35, 28, 41, 33, 30, 29, 31, 30]  # 9/10 hit 30+
        }),
        'Nikola Jokic': pd.DataFrame({
            'GAME_DATE': pd.date_range('2025-10-30', periods=10, freq='2D'),
            'AST': [11, 9, 13, 10, 16, 12, 9, 10, 11, 14]  # 10/10 hit 9+
        }),
        'Shai Gilgeous-Alexander': pd.DataFrame({
            'GAME_DATE': pd.date_range('2025-10-30', periods=10, freq='2D'),
            'PTS': [30, 35, 30, 30, 31, 23, 32, 33, 28, 55]  # 9/10 hit 30+
        }),
        'Anthony Davis': pd.DataFrame({
            'GAME_DATE': pd.date_range('2025-10-30', periods=10, freq='2D'),
            'REB': [13, 10, 11, 4, 12, 11, 10, 13, 4, 11]  # 8/10 hit 10+
        })
    }

    filepath = create_value_picks_graphic(mock_opportunities, mock_games)
    print(f"\n✅ Test graphic created!")
    print(f"📁 Open: {filepath}")


if __name__ == "__main__":
    main()
