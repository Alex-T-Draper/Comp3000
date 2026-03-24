"""Generate gaze heatmaps from eye tracking data."""

import sys
from pathlib import Path

# Allow running as standalone script from the visualisations folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

from gaze_utils import (DB_PATH, HEATMAP_DIR, SCREEN_W, SCREEN_H,
                         get_sessions, get_gaze_points, session_label)


def make_heatmap(gaze_x, gaze_y, title, output_path, sigma=30):
    """Generate and save a gaze heatmap."""
    # Convert normalised 0-1 coords to pixel coords
    px = (gaze_x * SCREEN_W).astype(int)
    py = (gaze_y * SCREEN_H).astype(int)

    # Clamp to screen bounds
    px = np.clip(px, 0, SCREEN_W - 1)
    py = np.clip(py, 0, SCREEN_H - 1)

    # Build 2D histogram
    heatmap, _, _ = np.histogram2d(py, px,
                                   bins=[SCREEN_H // 2, SCREEN_W // 2],
                                   range=[[0, SCREEN_H], [0, SCREEN_W]])

    # Smooth with Gaussian filter
    heatmap = gaussian_filter(heatmap, sigma=sigma)

    # Plot
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.imshow(heatmap, cmap='hot', interpolation='bilinear',
              extent=[0, SCREEN_W, SCREEN_H, 0], aspect='auto')
    ax.set_title(title, fontsize=14, pad=10)
    ax.set_xlabel('Screen X (px)')
    ax.set_ylabel('Screen Y (px)')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {output_path}")


def main():
    HEATMAP_DIR.mkdir(parents=True, exist_ok=True)
    sessions = get_sessions()

    if not sessions:
        print("No gaze data found in the database.")
        return

    print(f"Found {len(sessions)} session(s) with gaze data.\n")

    # Per-session heatmaps
    for row in sessions:
        session_id = row[0]
        total, valid = row[4], row[5]
        tos_label, cond_label, user_label = session_label(row)

        print(f"Session: {session_id}")
        print(f"  User: {user_label} | ToS: {tos_label} | Condition: {cond_label} | Samples: {valid}/{total}")

        gaze_x, gaze_y = get_gaze_points(session_id)
        if gaze_x is None or len(gaze_x) < 10:
            print("  Skipping — too few valid samples.")
            continue

        title = f"Gaze Heatmap — {user_label} — {tos_label} ({cond_label})"
        filename = f"heatmap_{user_label}_{tos_label}_{cond_label}_{session_id[:15]}.png"
        make_heatmap(gaze_x, gaze_y, title, HEATMAP_DIR / filename)

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
            SELECT g.gaze_x, g.gaze_y
            FROM gaze_samples g
            JOIN sessions s ON g.session_id = s.session_id
            WHERE s.condition_group = ? AND g.gaze_valid = 1
              AND g.gaze_x IS NOT NULL AND g.gaze_y IS NOT NULL
        ''', (condition,)).fetchall()
        conn.close()

        if len(rows) < 10:
            continue

        data = np.array(rows)
        title = f"Combined Gaze Heatmap — Condition: {condition}"
        filename = f"heatmap_combined_{condition}.png"
        print(f"Condition: {condition} ({len(rows)} samples)")
        make_heatmap(data[:, 0], data[:, 1], title, HEATMAP_DIR / filename)

    print(f"\nAll heatmaps saved to: {HEATMAP_DIR.resolve()}")


if __name__ == "__main__":
    main()
