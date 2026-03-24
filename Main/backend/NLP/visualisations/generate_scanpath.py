"""Generate scanpath visualisations from eye tracking data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from gaze_utils import (SCANPATH_DIR, SCREEN_W, SCREEN_H,
                         get_sessions, get_gaze_points_with_time,
                         detect_fixations, session_label)


def make_scanpath(gaze_x, gaze_y, timestamps, title, output_path):
    """Generate and save a scanpath visualisation with fixations and saccades."""
    fixations = detect_fixations(gaze_x, gaze_y, timestamps)
    if len(fixations) < 2:
        print("  Skipping scanpath — too few fixations detected.")
        return

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, SCREEN_W)
    ax.set_ylim(SCREEN_H, 0)
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_aspect('equal')

    fx = [f['x'] * SCREEN_W for f in fixations]
    fy = [f['y'] * SCREEN_H for f in fixations]
    durations = [f['duration_ms'] for f in fixations]

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
    SCANPATH_DIR.mkdir(parents=True, exist_ok=True)
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

        title = f"Scanpath — {user_label} — {tos_label} ({cond_label})"
        filename = f"scanpath_{user_label}_{tos_label}_{cond_label}_{session_id[:15]}.png"
        make_scanpath(gx, gy, ts, title, SCANPATH_DIR / filename)

    print(f"\nAll scanpaths saved to: {SCANPATH_DIR.resolve()}")


if __name__ == "__main__":
    main()
