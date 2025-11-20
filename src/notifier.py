#!/usr/bin/env python3
"""
Slack notification module for FlooorGang alerts.
Sends error notifications and success confirmations to Slack.
"""

import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def send_slack_notification(message, title=None, is_error=False):
    """
    Send a notification to Slack via webhook.

    Args:
        message: The notification message
        title: Optional title/header for the message
        is_error: If True, formats as error (with emoji)

    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("⚠️  SLACK_WEBHOOK_URL not set in environment - skipping notification")
        return False

    # Format timestamp
    pst = ZoneInfo("America/Los_Angeles")
    timestamp = datetime.now(pst).strftime('%Y-%m-%d %I:%M %p %Z')

    # Build message blocks for rich formatting
    blocks = []

    # Add header if title provided
    if title:
        emoji = "🚨" if is_error else "✅"
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {title}"
            }
        })

    # Add main message
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": message
        }
    })

    # Add timestamp footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"⏰ {timestamp}"
            }
        ]
    })

    payload = {"blocks": blocks}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Failed to send Slack notification: {e}")
        return False


def notify_scanner_success(num_picks, top_picks=None, first_game_time=None, graphic_path=None):
    """
    Notify that scanner ran successfully with detailed summary

    Args:
        num_picks: Total number of picks generated
        top_picks: List of top 3-4 picks (optional)
        first_game_time: String like "4:30 PM PST" (optional)
        graphic_path: Path to generated graphic file (optional)
    """
    message = f"*Picks generated:* {num_picks}"

    if first_game_time:
        message += f"\n*First game:* {first_game_time}"

    if top_picks and len(top_picks) > 0:
        message += f"\n\n*Top picks:*\n"
        for pick in top_picks[:4]:  # Limit to 4
            # Handle both player and team picks
            entity = pick.get('player') or pick.get('team')
            stat = pick.get('stat', '')  # Player picks have 'stat'
            pick_type = pick.get('type', '')  # Team picks have 'type' (OVER/UNDER)
            line = pick.get('line', 0)
            floor = pick.get('floor') or pick.get('ceiling', 0)

            # Format: "Player AST O7.5" or "Team O125.5"
            if stat:  # Player pick
                message += f"• {entity} {stat} O{line} (floor: {floor})\n"
            else:  # Team pick
                message += f"• {entity} {pick_type} {line} (floor: {floor})\n"

    if graphic_path:
        message += f"\n📊 Graphic saved to: `{graphic_path}`"

    return send_slack_notification(message, title="Scanner Success", is_error=False)


def notify_scanner_error(error_message, traceback_str=None):
    """Notify that scanner failed"""
    message = f"Scanner failed with error:\n\n```{error_message}```"

    if traceback_str:
        # Truncate traceback if too long (Slack has message limits)
        max_traceback_len = 2000
        if len(traceback_str) > max_traceback_len:
            traceback_str = traceback_str[-max_traceback_len:] + "\n... (truncated)"
        message += f"\n\n*Traceback:*\n```{traceback_str}```"

    return send_slack_notification(message, title="Scanner Failed", is_error=True)


def notify_scheduler_success(game_info, scheduled_time):
    """Notify that scheduler ran and scheduled scanner"""
    message = f"Scheduler ran successfully!\n\n*First game:* {game_info}\n*Scanner scheduled for:* {scheduled_time}"
    return send_slack_notification(message, title="Scheduler Success", is_error=False)


def notify_scheduler_no_games():
    """Notify that scheduler ran but found no games"""
    message = "No games found for today - scanner not scheduled."
    return send_slack_notification(message, title="Scheduler - No Games", is_error=False)


def notify_scheduler_error(error_message, traceback_str=None):
    """Notify that scheduler failed"""
    message = f"Scheduler failed with error:\n\n```{error_message}```"

    if traceback_str:
        max_traceback_len = 2000
        if len(traceback_str) > max_traceback_len:
            traceback_str = traceback_str[-max_traceback_len:] + "\n... (truncated)"
        message += f"\n\n*Traceback:*\n```{traceback_str}```"

    return send_slack_notification(message, title="Scheduler Failed", is_error=True)


def notify_results_tracker_success(date, num_scored, hit_count=None, miss_count=None, hit_rate=None, best_pick=None, worst_pick=None):
    """
    Notify that results tracker ran successfully with detailed stats

    Args:
        date: Date scored (YYYY-MM-DD)
        num_scored: Total picks scored
        hit_count: Number of hits
        miss_count: Number of misses
        hit_rate: Hit rate percentage
        best_pick: Dict with best performing pick info
        worst_pick: Dict with worst performing pick info
    """
    message = f"*Date:* {date}\n*Picks scored:* {num_scored}"

    if hit_count is not None and miss_count is not None:
        message += f"\n*Results:* {hit_count} hits / {miss_count} misses"

    if hit_rate is not None:
        message += f"\n*Hit rate:* **{hit_rate:.1f}%**"

    if best_pick:
        entity = best_pick['entity']
        stat = best_pick['stat']
        line = best_pick['line']
        actual = best_pick['actual']
        message += f"\n\n🔥 *Best:* {entity} ({actual} {stat} on {line} line)"

    if worst_pick:
        entity = worst_pick['entity']
        stat = worst_pick['stat']
        line = worst_pick['line']
        actual = worst_pick['actual']
        floor = worst_pick.get('floor', 0)
        message += f"\n❌ *Worst:* {entity} ({actual} {stat} on {line} line, floor: {floor})"

    return send_slack_notification(message, title="Results Tracker Success", is_error=False)


def notify_results_tracker_error(error_message, traceback_str=None):
    """Notify that results tracker failed"""
    message = f"Results tracker failed with error:\n\n```{error_message}```"

    if traceback_str:
        max_traceback_len = 2000
        if len(traceback_str) > max_traceback_len:
            traceback_str = traceback_str[-max_traceback_len:] + "\n... (truncated)"
        message += f"\n\n*Traceback:*\n```{traceback_str}```"

    return send_slack_notification(message, title="Results Tracker Failed", is_error=True)


if __name__ == "__main__":
    # Test notification
    print("Testing Slack notification...")
    success = send_slack_notification(
        "This is a test notification from FlooorGang!",
        title="Test Notification",
        is_error=False
    )
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Test notification failed")
