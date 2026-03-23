"""Generate Areas-of-Interest (AOI) analysis from eye tracking data.

Divides the screen into a grid of rectangular AOIs and computes:
  - number of fixations per AOI
  - total dwell time per AOI
  - percentage of total fixation time per AOI

Produces two visualisations per session:
  1. AOI fixation count grid
  2. AOI dwell-time grid
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle

from gaze_utils import (AOI_DIR, SCREEN_W, SCREEN_H,
                         get_sessions, get_gaze_points_with_time,
                         detect_fixations, session_label)

# Grid dimensions (columns x rows)
AOI_COLS = 4
AOI_ROWS = 3

AOI_LABELS = [
    "Top-Left",    "Top-Centre-Left",    "Top-Centre-Right",    "Top-Right",
    "Mid-Left",    "Mid-Centre-Left",    "Mid-Centre-Right",    "Mid-Right",
    "Bottom-Left", "Bottom-Centre-Left", "Bottom-Centre-Right", "Bottom-Right",
]


def compute_aoi_stats(fixations):
    """Assign each fixation to an AOI cell and compute per-cell stats.

    Returns:
        count_grid: (AOI_ROWS, AOI_COLS) array of fixation counts
        dwell_grid: (AOI_ROWS, AOI_COLS) array of total dwell time (ms)
    """
    count_grid = np.zeros((AOI_ROWS, AOI_COLS), dtype=int)
    dwell_grid = np.zeros((AOI_ROWS, AOI_COLS), dtype=float)

    cell_w = 1.0 / AOI_COLS
    cell_h = 1.0 / AOI_ROWS

    for f in fixations:
        col = min(int(f['x'] / cell_w), AOI_COLS - 1)
        row = min(int(f['y'] / cell_h), AOI_ROWS - 1)
        count_grid[row, col] += 1
        dwell_grid[row, col] += f['duration_ms']

    return count_grid, dwell_grid


def _draw_aoi_grid(ax, grid, title, cmap, value_fmt, label):
    """Render a colour-coded AOI grid with value annotations."""
    ax.set_xlim(0, SCREEN_W)
    ax.set_ylim(SCREEN_H, 0)
    ax.set_aspect('equal')

    cell_w_px = SCREEN_W / AOI_COLS
    cell_h_px = SCREEN_H / AOI_ROWS

    vmax = grid.max() if grid.max() > 0 else 1
    norm = Normalize(vmin=0, vmax=vmax)
    colourmap = plt.get_cmap(cmap)

    for r in range(AOI_ROWS):
        for c in range(AOI_COLS):
            val = grid[r, c]
            colour = colourmap(norm(val))
            rect = Rectangle((c * cell_w_px, r * cell_h_px),
                              cell_w_px, cell_h_px,
                              facecolor=colour, edgecolor='white',
                              linewidth=1.5, alpha=0.85)
            ax.add_patch(rect)

            # Cell value
            cx = c * cell_w_px + cell_w_px / 2
            cy = r * cell_h_px + cell_h_px / 2

            # Choose text colour for contrast
            brightness = 0.299 * colour[0] + 0.587 * colour[1] + 0.114 * colour[2]
            txt_colour = 'white' if brightness < 0.5 else '#1a1a1a'

            ax.text(cx, cy - 15, value_fmt.format(val),
                    ha='center', va='center', fontsize=16,
                    fontweight='bold', color=txt_colour, zorder=3)

            # AOI label
            idx = r * AOI_COLS + c
            if idx < len(AOI_LABELS):
                ax.text(cx, cy + 20, AOI_LABELS[idx],
                        ha='center', va='center', fontsize=8,
                        color=txt_colour, alpha=0.7, zorder=3)

    ax.set_title(title, fontsize=14, pad=10)
    ax.set_xlabel('Screen X (px)')
    ax.set_ylabel('Screen Y (px)')


def make_aoi(gaze_x, gaze_y, timestamps, title_prefix, output_prefix):
    """Generate AOI fixation-count and dwell-time grids."""
    fixations = detect_fixations(gaze_x, gaze_y, timestamps)
    if len(fixations) < 2:
        print("  Skipping AOI — too few fixations detected.")
        return

    count_grid, dwell_grid = compute_aoi_stats(fixations)
    total_dwell = dwell_grid.sum()

    # --- Fixation count grid ---
    fig, ax = plt.subplots(figsize=(16, 9))
    _draw_aoi_grid(ax, count_grid,
                   f"{title_prefix} — Fixation Count per AOI",
                   'Blues', '{:.0f}', 'fixations')
    fig.tight_layout()
    count_path = AOI_DIR / f"{output_prefix}_aoi_count.png"
    fig.savefig(count_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {count_path}")

    # --- Dwell time grid (absolute ms + percentage) ---
    fig, ax = plt.subplots(figsize=(16, 9))

    ax.set_xlim(0, SCREEN_W)
    ax.set_ylim(SCREEN_H, 0)
    ax.set_aspect('equal')

    cell_w_px = SCREEN_W / AOI_COLS
    cell_h_px = SCREEN_H / AOI_ROWS

    vmax = dwell_grid.max() if dwell_grid.max() > 0 else 1
    norm = Normalize(vmin=0, vmax=vmax)
    colourmap = plt.get_cmap('OrRd')

    for r in range(AOI_ROWS):
        for c in range(AOI_COLS):
            val = dwell_grid[r, c]
            pct = (val / total_dwell * 100) if total_dwell > 0 else 0
            colour = colourmap(norm(val))
            rect = Rectangle((c * cell_w_px, r * cell_h_px),
                              cell_w_px, cell_h_px,
                              facecolor=colour, edgecolor='white',
                              linewidth=1.5, alpha=0.85)
            ax.add_patch(rect)

            cx = c * cell_w_px + cell_w_px / 2
            cy = r * cell_h_px + cell_h_px / 2

            brightness = 0.299 * colour[0] + 0.587 * colour[1] + 0.114 * colour[2]
            txt_colour = 'white' if brightness < 0.5 else '#1a1a1a'

            ax.text(cx, cy - 20, f"{val:.0f} ms",
                    ha='center', va='center', fontsize=14,
                    fontweight='bold', color=txt_colour, zorder=3)
            ax.text(cx, cy + 10, f"({pct:.1f}%)",
                    ha='center', va='center', fontsize=11,
                    color=txt_colour, alpha=0.8, zorder=3)

            idx = r * AOI_COLS + c
            if idx < len(AOI_LABELS):
                ax.text(cx, cy + 35, AOI_LABELS[idx],
                        ha='center', va='center', fontsize=8,
                        color=txt_colour, alpha=0.6, zorder=3)

    ax.set_title(f"{title_prefix} — Dwell Time per AOI", fontsize=14, pad=10)
    ax.set_xlabel('Screen X (px)')
    ax.set_ylabel('Screen Y (px)')

    fig.tight_layout()
    dwell_path = AOI_DIR / f"{output_prefix}_aoi_dwell.png"
    fig.savefig(dwell_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {dwell_path}")

    # Print summary table
    print(f"  {'AOI':<25} {'Fixations':>10} {'Dwell (ms)':>12} {'%':>8}")
    print(f"  {'─' * 57}")
    for r in range(AOI_ROWS):
        for c in range(AOI_COLS):
            idx = r * AOI_COLS + c
            name = AOI_LABELS[idx] if idx < len(AOI_LABELS) else f"({r},{c})"
            cnt = count_grid[r, c]
            dwl = dwell_grid[r, c]
            pct = (dwl / total_dwell * 100) if total_dwell > 0 else 0
            print(f"  {name:<25} {cnt:>10} {dwl:>12.0f} {pct:>7.1f}%")


def main():
    AOI_DIR.mkdir(parents=True, exist_ok=True)
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

        title_prefix = f"{user_label} — {tos_label} ({cond_label})"
        out_prefix = f"{user_label}_{tos_label}_{cond_label}_{session_id[:15]}"
        make_aoi(gx, gy, ts, title_prefix, out_prefix)

    print(f"\nAll AOI charts saved to: {AOI_DIR.resolve()}")


if __name__ == "__main__":
    main()
