"""Generate scanpath visualisations from eye tracking data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import matplotlib.pyplot as plt

from gaze_utils import (SCANPATH_DIR, SCREEN_W, SCREEN_H,
                         get_sessions, get_gaze_points_with_time,
                         detect_fixations, session_label, apply_scroll_adjustment)


def make_scanpath_from_pixels(px, py, timestamps, title, output_path):
    """Generate scanpath from scroll-adjusted pixel coordinates."""
    
    # Convert pixels back to normalized for fixation detection
    # (detect_fixations expects 0-1 normalized coords)
    content_height = max(SCREEN_H, py.max() + 100) if len(py) > 0 else SCREEN_H
    gx_norm = px / SCREEN_W
    gy_norm = py / content_height
    
    fixations = detect_fixations(gx_norm, gy_norm, timestamps)
    if len(fixations) < 2:
        print("  Skipping scanpath — too few fixations detected.")
        return

    # Convert fixations back to pixels
    fx = [f['x'] * SCREEN_W for f in fixations]
    fy = [f['y'] * content_height for f in fixations]
    durations = [f['duration_ms'] for f in fixations]

    # Adjust figure height for content
    fig_height = max(9, (content_height / SCREEN_W) * 16)
    fig, ax = plt.subplots(figsize=(16, fig_height))
    ax.set_xlim(0, SCREEN_W)
    ax.set_ylim(content_height, 0)
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_aspect('equal')

    # Saccade lines
    for k in range(len(fixations) - 1):
        ax.plot([fx[k], fx[k + 1]], [fy[k], fy[k + 1]],
                color='#e94560', alpha=0.5, linewidth=1.2, zorder=1)

    # Fixation circles — size proportional to duration
    max_dur = max(durations)
    min_size, max_size = 40, 500
    sizes = [min_size + (d / max_dur) * (max_size - min_size) for d in durations]

    scatter = ax.scatter(fx, fy, s=sizes, c=range(len(fixations)),
                         cmap='plasma', alpha=0.8, edgecolors='white',
                         linewidths=0.6, zorder=2)

    # Number labels
    for k, (x, y) in enumerate(zip(fx, fy), 1):
        ax.text(x, y, str(k), ha='center', va='center',
                fontsize=7, color='white', fontweight='bold', zorder=3)

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Fixation order', color='white', fontsize=10)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')

    ax.set_title(title, fontsize=14, pad=10, color='white')
    ax.set_xlabel('Screen X (px)', color='white')
    ax.set_ylabel('Content Y (px)', color='white') 
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('#333')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {output_path} ({len(fixations)} fixations)")


def main():
    import sys
    SCANPATH_DIR.mkdir(parents=True, exist_ok=True)
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

        title = f"Scanpath — {user_label} — {tos_label} ({cond_label})"
        filename = f"scanpath_{user_label}_{tos_label}_{cond_label}_{session_id[:15]}.png"
        make_scanpath_from_pixels(px, py, ts, title, SCANPATH_DIR / filename)

    print(f"\nAll scanpaths saved to: {SCANPATH_DIR.resolve()}")


if __name__ == "__main__":
    main()