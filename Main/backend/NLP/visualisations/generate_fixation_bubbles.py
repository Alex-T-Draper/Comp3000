"""Generate fixation duration bubble charts from eye tracking data.

Each bubble is centred on a fixation location with radius proportional to
how long the participant fixated there.  Colour encodes duration so that
longer fixations stand out immediately.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from gaze_utils import (DB_PATH, BUBBLES_DIR, SCREEN_W, SCREEN_H, apply_scroll_adjustment,
                         get_sessions, get_gaze_points_with_time,
                         detect_fixations, session_label)


def make_fixation_bubbles_from_pixels(px, py, timestamps, title, output_path, bg_image=None):
    """Bubble chart from scroll-adjusted pixel coordinates."""
    
    # Determine canvas dimensions
    if bg_image is not None:
        content_height = bg_image.shape[0]
        canvas_width = bg_image.shape[1]
    else:
        content_height = max(SCREEN_H, py.max() + 100) if len(py) > 0 else SCREEN_H
        canvas_width = SCREEN_W
    
    # Convert pixels to normalized for fixation detection
    gx_norm = px / canvas_width
    gy_norm = py / content_height
    
    fixations = detect_fixations(gx_norm, gy_norm, timestamps)
    if len(fixations) < 2:
        print("  Skipping — too few fixations detected.")
        return

    # Convert fixations to pixels
    fx = np.array([f['x'] * canvas_width for f in fixations])
    fy = np.array([f['y'] * content_height for f in fixations])
    durations = np.array([f['duration_ms'] for f in fixations])

    # Adjust figure for content height
    fig_height = max(9, (content_height / canvas_width) * 16)
    fig, ax = plt.subplots(figsize=(16, fig_height))
    ax.set_xlim(0, canvas_width)
    ax.set_ylim(content_height, 0)
    ax.set_aspect('equal')

    # Theme: light when document background, dark otherwise
    if bg_image is not None:
        ax.imshow(bg_image, extent=[0, canvas_width, content_height, 0],
                  aspect='auto', alpha=0.5)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        txt_color, stats_color, spine_color = 'black', '#555555', '#ccc'
    else:
        ax.set_facecolor('#0f0f1a')
        fig.patch.set_facecolor('#0f0f1a')
        txt_color, stats_color, spine_color = 'white', '#aaaaaa', '#333'

    # Scale bubble sizes: area proportional to duration
    max_dur = durations.max()
    min_area, max_area = 80, 2000
    areas = min_area + (durations / max_dur) * (max_area - min_area)

    norm = Normalize(vmin=durations.min(), vmax=max_dur)

    scatter = ax.scatter(fx, fy, s=areas, c=durations, cmap='YlOrRd',
                         norm=norm, alpha=0.75, edgecolors='white',
                         linewidths=0.5, zorder=2)

    # Duration labels on the larger bubbles (top quartile)
    threshold = np.percentile(durations, 75)
    for i, f in enumerate(fixations):
        if f['duration_ms'] >= threshold:
            ax.text(fx[i], fy[i],  
                    f"{f['duration_ms']:.0f}ms",
                    ha='center', va='center', fontsize=6,
                    color='white', fontweight='bold', zorder=3)

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Fixation duration (ms)', color=txt_color, fontsize=10)
    cbar.ax.yaxis.set_tick_params(color=txt_color)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=txt_color)

    # Stats annotation
    stats_text = (f"Fixations: {len(fixations)}  |  "
                  f"Mean: {durations.mean():.0f} ms  |  "
                  f"Max: {max_dur:.0f} ms  |  "
                  f"Total: {durations.sum():.0f} ms")
    ax.text(0.5, 1.02, stats_text, transform=ax.transAxes,
            ha='center', va='bottom', fontsize=9, color=stats_color)

    ax.set_title(title, fontsize=14, pad=25, color=txt_color)
    ax.set_xlabel('Screen X (px)', color=txt_color)
    ax.set_ylabel('Content Y (px)', color=txt_color)
    ax.tick_params(colors=txt_color)
    for spine in ax.spines.values():
        spine.set_color(spine_color)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {output_path} ({len(fixations)} fixations)")


def main():
    import sys
    BUBBLES_DIR.mkdir(parents=True, exist_ok=True)
    user_filter = sys.argv[1] if len(sys.argv) > 1 else None
    sessions = get_sessions()
    if user_filter:
        sessions = [row for row in sessions if row[3] == user_filter]
    if not sessions:
        print("No gaze data found in the database for the specified user." if user_filter else "No gaze data found in the database.")
        return
    print(f"Found {len(sessions)} session(s) with gaze data.\n")

    for row in sessions:
        session_id = row[0]
        total, valid = row[4], row[5]
        tos_label, cond_label, user_label = session_label(row)

        print(f"Session: {session_id}")
        print(f"  User: {user_label} | ToS: {tos_label} | Condition: {cond_label} | Samples: {valid}/{total}")

        gx, gy, ts, scroll_pos = get_gaze_points_with_time(session_id)
        if gx is None or len(gx) < 10:
            print("  Skipping — too few valid samples.")
            continue
        
        # Apply scroll adjustment
        px, py = apply_scroll_adjustment(gx, gy, scroll_pos)

        title = f"Fixation Bubbles — {user_label} — {tos_label} ({cond_label})"
        filename = f"bubbles_{user_label}_{tos_label}_{cond_label}_{session_id[:15]}.png"
        make_fixation_bubbles_from_pixels(px, py, ts, title, BUBBLES_DIR / filename)

    # Combined bubbles per condition group
    print("\n--- Combined fixation bubbles by condition ---")
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
            SELECT g.gaze_x, g.gaze_y, g.device_ts, g.scroll_position
            FROM gaze_samples g
            JOIN sessions s ON g.session_id = s.session_id
            WHERE s.condition_group = ? AND g.gaze_valid = 1
              AND g.gaze_x IS NOT NULL AND g.gaze_y IS NOT NULL
            ORDER BY g.device_ts
        ''', (condition,)).fetchall()
        conn.close()

        if len(rows) < 10:
            continue

        data = np.array(rows)
        gaze_x = data[:, 0]
        gaze_y = data[:, 1]
        timestamps = data[:, 2]
        scroll_pos = data[:, 3]

        px, py = apply_scroll_adjustment(gaze_x, gaze_y, scroll_pos)

        print(f"Condition: {condition} ({len(rows)} samples)")
        title = f"Combined Fixation Bubbles — Condition: {condition}"
        filename = f"bubbles_combined_{condition}.png"
        make_fixation_bubbles_from_pixels(px, py, timestamps, title, BUBBLES_DIR / filename)

    print(f"\nAll fixation bubble charts saved to: {BUBBLES_DIR.resolve()}")


if __name__ == "__main__":
    main()