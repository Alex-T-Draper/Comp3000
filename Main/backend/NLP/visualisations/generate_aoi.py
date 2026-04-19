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

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle

from gaze_utils import (DB_PATH, AOI_DIR, SCREEN_W, SCREEN_H, apply_scroll_adjustment,
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


def _draw_aoi_grid(ax, grid, title, cmap, value_fmt, label, content_height,
                   canvas_width=SCREEN_W, rect_alpha=0.85):
    """Render a colour-coded AOI grid with value annotations."""
    ax.set_xlim(0, canvas_width)
    ax.set_ylim(content_height, 0)  
    ax.set_aspect('equal')

    cell_w_px = canvas_width / AOI_COLS
    cell_h_px = content_height / AOI_ROWS  

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
                              linewidth=1.5, alpha=rect_alpha)
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
    ax.set_ylabel('Content Y (px)')


def make_aoi_from_pixels(px, py, timestamps, title_prefix, output_prefix,
                         bg_image=None, output_dir=None):
    """Generate AOI grids from scroll-adjusted pixel coordinates."""
    if output_dir is None:
        output_dir = AOI_DIR
    
    # Determine canvas dimensions
    if bg_image is not None:
        content_height = bg_image.shape[0]
        canvas_width = bg_image.shape[1]
    else:
        content_height = max(SCREEN_H, py.max() + 100) if len(py) > 0 else SCREEN_H
        canvas_width = SCREEN_W
    
    # Convert to normalized for fixation detection
    gx_norm = px / canvas_width
    gy_norm = py / content_height
    
    fixations = detect_fixations(gx_norm, gy_norm, timestamps)
    if len(fixations) < 2:
        print("  Skipping AOI — too few fixations detected.")
        return

    count_grid, dwell_grid = compute_aoi_stats(fixations)
    total_dwell = dwell_grid.sum()

    # Adjust figure height
    fig_height = max(9, (content_height / canvas_width) * 16)
    rect_alpha = 0.5 if bg_image is not None else 0.85

    # --- Fixation count grid ---
    fig, ax = plt.subplots(figsize=(16, fig_height))
    if bg_image is not None:
        ax.imshow(bg_image, extent=[0, canvas_width, content_height, 0], aspect='auto')
    _draw_aoi_grid(ax, count_grid,
                   f"{title_prefix} — Fixation Count per AOI",
                   'Blues', '{:.0f}', 'fixations', content_height,
                   canvas_width=canvas_width, rect_alpha=rect_alpha)
    fig.tight_layout()
    count_path = output_dir / f"{output_prefix}_aoi_count.png"
    fig.savefig(count_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {count_path}")

    # --- Dwell time grid (absolute ms + percentage) ---
    fig, ax = plt.subplots(figsize=(16, fig_height))

    if bg_image is not None:
        ax.imshow(bg_image, extent=[0, canvas_width, content_height, 0], aspect='auto')

    ax.set_xlim(0, canvas_width)
    ax.set_ylim(content_height, 0)
    ax.set_aspect('equal')

    cell_w_px = canvas_width / AOI_COLS
    cell_h_px = content_height / AOI_ROWS  

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
                              linewidth=1.5, alpha=rect_alpha)
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
    ax.set_ylabel('Content Y (px)')

    fig.tight_layout()
    dwell_path = output_dir / f"{output_prefix}_aoi_dwell.png"
    fig.savefig(dwell_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {dwell_path}")

    # Print summary table
    print(f"  {'AOI':<25} {'Fixations':>10} {'Dwell (ms)':>12} {'%':>8}")
    print(f"  {'-' * 57}")
    for r in range(AOI_ROWS):
        for c in range(AOI_COLS):
            idx = r * AOI_COLS + c
            name = AOI_LABELS[idx] if idx < len(AOI_LABELS) else f"({r},{c})"
            cnt = count_grid[r, c]
            dwl = dwell_grid[r, c]
            pct = (dwl / total_dwell * 100) if total_dwell > 0 else 0
            print(f"  {name:<25} {cnt:>10} {dwl:>12.0f} {pct:>7.1f}%")


def main():
    import sys
    AOI_DIR.mkdir(parents=True, exist_ok=True)
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

        title_prefix = f"{user_label} — {tos_label} ({cond_label})"
        out_prefix = f"{user_label}_{tos_label}_{cond_label}_{session_id[:15]}"
        make_aoi_from_pixels(px, py, ts, title_prefix, out_prefix)

    # Combined AOI per condition group
    print("\n--- Combined AOI charts by condition ---")
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
        title_prefix = f"Combined — Condition: {condition}"
        out_prefix = f"combined_{condition}"
        make_aoi_from_pixels(px, py, timestamps, title_prefix, out_prefix)

    print(f"\nAll AOI charts saved to: {AOI_DIR.resolve()}")


if __name__ == "__main__":
    main()