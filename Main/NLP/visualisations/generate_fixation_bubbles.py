"""Generate fixation duration bubble charts from eye tracking data.

Each bubble is centred on a fixation location with radius proportional to
how long the participant fixated there.  Colour encodes duration so that
longer fixations stand out immediately.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from gaze_utils import (BUBBLES_DIR, SCREEN_W, SCREEN_H,
                         get_sessions, get_gaze_points_with_time,
                         detect_fixations, session_label)


def make_fixation_bubbles(gaze_x, gaze_y, timestamps, title, output_path):
    """Bubble chart where each circle = one fixation, sized by duration."""
    fixations = detect_fixations(gaze_x, gaze_y, timestamps)
    if len(fixations) < 2:
        print("  Skipping — too few fixations detected.")
        return

    fx = np.array([f['x'] * SCREEN_W for f in fixations])
    fy = np.array([f['y'] * SCREEN_H for f in fixations])
    durations = np.array([f['duration_ms'] for f in fixations])

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, SCREEN_W)
    ax.set_ylim(SCREEN_H, 0)
    ax.set_facecolor('#0f0f1a')
    fig.patch.set_facecolor('#0f0f1a')
    ax.set_aspect('equal')

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
    for f in fixations:
        if f['duration_ms'] >= threshold:
            ax.text(f['x'] * SCREEN_W, f['y'] * SCREEN_H,
                    f"{f['duration_ms']:.0f}ms",
                    ha='center', va='center', fontsize=6,
                    color='white', fontweight='bold', zorder=3)

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Fixation duration (ms)', color='white', fontsize=10)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')

    # Stats annotation
    stats_text = (f"Fixations: {len(fixations)}  |  "
                  f"Mean: {durations.mean():.0f} ms  |  "
                  f"Max: {max_dur:.0f} ms  |  "
                  f"Total: {durations.sum():.0f} ms")
    ax.text(0.5, 1.02, stats_text, transform=ax.transAxes,
            ha='center', va='bottom', fontsize=9, color='#aaaaaa')

    ax.set_title(title, fontsize=14, pad=25, color='white')
    ax.set_xlabel('Screen X (px)', color='white')
    ax.set_ylabel('Screen Y (px)', color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('#333')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {output_path} ({len(fixations)} fixations)")


def main():
    BUBBLES_DIR.mkdir(parents=True, exist_ok=True)
    sessions = get_sessions()

    if not sessions:
        print("No gaze data found in the database.")
        return

    print(f"Found {len(sessions)} session(s) with gaze data.\n")

    for row in sessions:
        session_id = row[0]
        total, valid = row[4], row[5]
        tos_label, cond_label, user_label = session_label(row)

        print(f"Session: {session_id}")
        print(f"  User: {user_label} | ToS: {tos_label} | Condition: {cond_label} | Samples: {valid}/{total}")

        gx, gy, ts = get_gaze_points_with_time(session_id)
        if gx is None or len(gx) < 10:
            print("  Skipping — too few valid samples.")
            continue

        title = f"Fixation Bubbles — {user_label} — {tos_label} ({cond_label})"
        filename = f"bubbles_{user_label}_{tos_label}_{cond_label}_{session_id[:15]}.png"
        make_fixation_bubbles(gx, gy, ts, title, BUBBLES_DIR / filename)

    print(f"\nAll fixation bubble charts saved to: {BUBBLES_DIR.resolve()}")


if __name__ == "__main__":
    main()
