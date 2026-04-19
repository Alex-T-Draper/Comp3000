"""Generate AOI analysis with document screenshots as background."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import numpy as np
import matplotlib.pyplot as plt

from gaze_utils import (DB_PATH, AOI_BG_DIR, SCREEN_W, SCREEN_H,
                         apply_scroll_adjustment, get_sessions,
                         get_gaze_points_with_time, session_label,
                         get_screenshot_path)
from generate_aoi import make_aoi_from_pixels


def main():
    AOI_BG_DIR.mkdir(parents=True, exist_ok=True)
    user_filter = sys.argv[1] if len(sys.argv) > 1 else None
    sessions = get_sessions()
    if user_filter:
        sessions = [row for row in sessions if row[3] == user_filter]
    if not sessions:
        print("No sessions found.")
        return
    print(f"Found {len(sessions)} session(s) with gaze data.\n")

    for row in sessions:
        session_id = row[0]
        total, valid = row[4], row[5]
        tos_label, cond_label, user_label = session_label(row)

        print(f"Session: {session_id}")
        print(f"  User: {user_label} | ToS: {tos_label} | Condition: {cond_label} | Samples: {valid}/{total}")

        bg_path = get_screenshot_path(cond_label)
        if not bg_path:
            print("  Skipping — no screenshot found.")
            continue

        gx, gy, ts, scroll_pos = get_gaze_points_with_time(session_id)
        if gx is None or len(gx) < 10:
            print("  Skipping — too few valid samples.")
            continue

        px, py = apply_scroll_adjustment(gx, gy, scroll_pos)
        bg = plt.imread(str(bg_path))

        title_prefix = f"{user_label} — {tos_label} ({cond_label})"
        out_prefix = f"{user_label}_{tos_label}_{cond_label}_{session_id[:15]}"
        make_aoi_from_pixels(px, py, ts, title_prefix, out_prefix,
                             bg_image=bg, output_dir=AOI_BG_DIR)

    # Combined per condition
    print("\n--- Combined AOI (with background) by condition ---")
    conn = sqlite3.connect(DB_PATH)
    conditions = conn.execute('''
        SELECT DISTINCT s.condition_group
        FROM gaze_samples g
        JOIN sessions s ON g.session_id = s.session_id
        WHERE s.condition_group IS NOT NULL
    ''').fetchall()
    conn.close()

    for (condition,) in conditions:
        bg_path = get_screenshot_path(condition)
        if not bg_path:
            continue

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
        px, py = apply_scroll_adjustment(data[:, 0], data[:, 1], data[:, 3])
        bg = plt.imread(str(bg_path))

        print(f"Condition: {condition} ({len(rows)} samples)")
        title_prefix = f"Combined — Condition: {condition}"
        out_prefix = f"combined_{condition}"
        make_aoi_from_pixels(px, py, data[:, 2], title_prefix, out_prefix,
                             bg_image=bg, output_dir=AOI_BG_DIR)

    print(f"\nAll AOI charts (with background) saved to: {AOI_BG_DIR.resolve()}")


if __name__ == "__main__":
    main()
