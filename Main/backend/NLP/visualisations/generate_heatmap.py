"""Generate gaze heatmaps from eye tracking data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

from gaze_utils import (DB_PATH, HEATMAP_DIR, SCREEN_W, SCREEN_H,
                         get_sessions, get_gaze_points, session_label,
                         apply_scroll_adjustment)


def make_heatmap_from_pixels(px, py, title, output_path, sigma=30):
    """Generate and save a gaze heatmap from pixel coordinates."""
    
    # Determine content height (max Y coordinate)
    content_height = max(SCREEN_H, int(py.max()) + 100) if len(py) > 0 else SCREEN_H
    
    # Clamp to bounds
    px = np.clip(px, 0, SCREEN_W - 1)
    py = np.clip(py, 0, content_height - 1)
    
    # Build 2D histogram
    heatmap, _, _ = np.histogram2d(py, px,
                                   bins=[content_height // 2, SCREEN_W // 2],
                                   range=[[0, content_height], [0, SCREEN_W]])
    
    # Smooth with Gaussian filter
    heatmap = gaussian_filter(heatmap, sigma=sigma)
    
    # Plot with adjusted height
    fig_height = max(9, (content_height / SCREEN_W) * 16)
    fig, ax = plt.subplots(figsize=(16, fig_height))
    ax.imshow(heatmap, cmap='hot', interpolation='bilinear',
              extent=[0, SCREEN_W, content_height, 0], aspect='auto')
    ax.set_title(title, fontsize=14, pad=10)
    ax.set_xlabel('Screen X (px)')
    ax.set_ylabel('Content Y (px)') 
    
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {output_path}")


def main():
    import sys
    HEATMAP_DIR.mkdir(parents=True, exist_ok=True)
    user_filter = sys.argv[1] if len(sys.argv) > 1 else None
    sessions = get_sessions()
    if user_filter:
        sessions = [row for row in sessions if row[3] == user_filter]
    if not sessions:
        print("No gaze data found in the database for the specified user." if user_filter else "No gaze data found in the database.")
        return
    print(f"Found {len(sessions)} session(s) with gaze data.\n")

    # Per-session heatmaps
    for row in sessions:
        session_id = row[0]
        total, valid = row[4], row[5]
        tos_label, cond_label, user_label = session_label(row)

        print(f"Session: {session_id}")
        print(f"  User: {user_label} | ToS: {tos_label} | Condition: {cond_label} | Samples: {valid}/{total}")

        gaze_x, gaze_y, scroll_pos = get_gaze_points(session_id)
        if gaze_x is None or len(gaze_x) < 10:
            print("  Skipping — too few valid samples.")
            continue

        # Apply scroll adjustment
        px, py = apply_scroll_adjustment(gaze_x, gaze_y, scroll_pos)

        title = f"Gaze Heatmap — {user_label} — {tos_label} ({cond_label})"
        filename = f"heatmap_{user_label}_{tos_label}_{cond_label}_{session_id[:15]}.png"
        make_heatmap_from_pixels(px, py, title, HEATMAP_DIR / filename)  # ✅ Fixed

    # Combined heatmap per condition group
    print("\n--- Combined heatmaps by condition ---")
    conn = sqlite3.connect(DB_PATH)
    conditions = conn.execute('''
        SELECT DISTINCT s.condition_group
        FROM gaze_samples g
        JOIN sessions s ON g.session_id = s.session_id
        WHERE s.condition_group IS NOT NULL
    ''').fetchall()
    conn.close()

    for (condition,) in conditions:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute('''
            SELECT g.gaze_x, g.gaze_y, g.scroll_position
            FROM gaze_samples g
            JOIN sessions s ON g.session_id = s.session_id
            WHERE s.condition_group = ? AND g.gaze_valid = 1
              AND g.gaze_x IS NOT NULL AND g.gaze_y IS NOT NULL
        ''', (condition,)).fetchall()
        conn.close()

        if len(rows) < 10:
            continue

        data = np.array(rows)
        gaze_x = data[:, 0]
        gaze_y = data[:, 1]
        scroll_pos = data[:, 2]
        
        # Apply scroll adjustment
        px, py = apply_scroll_adjustment(gaze_x, gaze_y, scroll_pos)
        
        title = f"Combined Gaze Heatmap — Condition: {condition}"
        filename = f"heatmap_combined_{condition}.png"
        print(f"Condition: {condition} ({len(rows)} samples)")
        make_heatmap_from_pixels(px, py, title, HEATMAP_DIR / filename) 

    print(f"\nAll heatmaps saved to: {HEATMAP_DIR.resolve()}")


if __name__ == "__main__":
    main()