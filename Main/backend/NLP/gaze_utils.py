"""Shared utilities for gaze data loading and fixation detection."""

import sqlite3
import numpy as np
from pathlib import Path

DB_PATH = Path(__file__).parent / "tos_research.db"
OUTPUT_BASE = Path(__file__).parent / "output"

# Per-visualisation output directories
HEATMAP_DIR = OUTPUT_BASE / "heatmaps"
SCANPATH_DIR = OUTPUT_BASE / "scanpaths"
BUBBLES_DIR = OUTPUT_BASE / "bubbles"
AOI_DIR = OUTPUT_BASE / "aoi"
SCREENSHOTS_DIR = OUTPUT_BASE / "screenshots"

# With-background subdirectories
HEATMAP_BG_DIR = HEATMAP_DIR / "with_background"
SCANPATH_BG_DIR = SCANPATH_DIR / "with_background"
BUBBLES_BG_DIR = BUBBLES_DIR / "with_background"
AOI_BG_DIR = AOI_DIR / "with_background"

# Screen resolution
SCREEN_W = 2560
SCREEN_H = 1440


def get_sessions():
    """Return all sessions that have gaze data."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('''
        SELECT g.session_id, s.tos_id, s.condition_group, u.name as user_name,
               COUNT(*) as total,
               SUM(CASE WHEN g.gaze_valid = 1 THEN 1 ELSE 0 END) as valid
        FROM gaze_samples g
        LEFT JOIN sessions s ON g.session_id = s.session_id
        LEFT JOIN users u ON s.user_id = u.id
        GROUP BY g.session_id
        ORDER BY MIN(g.timestamp)
    ''').fetchall()
    conn.close()
    return rows


def get_gaze_points(session_id):
    """Return valid gaze points for a session as numpy arrays with scroll adjustment."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('''
        SELECT gaze_x, gaze_y, scroll_position FROM gaze_samples
        WHERE session_id = ? AND gaze_valid = 1
          AND gaze_x IS NOT NULL AND gaze_y IS NOT NULL
        ORDER BY timestamp
    ''', (session_id,)).fetchall()
    conn.close()
    if not rows:
        return None, None, None
    data = np.array(rows)
    gaze_x = data[:, 0]
    gaze_y = data[:, 1]
    scroll_pos = data[:, 2]
    return gaze_x, gaze_y, scroll_pos


def get_gaze_points_with_time(session_id):
    """Return valid gaze points with device timestamps and scroll position."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('''
        SELECT gaze_x, gaze_y, device_ts, scroll_position FROM gaze_samples
        WHERE session_id = ? AND gaze_valid = 1
          AND gaze_x IS NOT NULL AND gaze_y IS NOT NULL
        ORDER BY device_ts
    ''', (session_id,)).fetchall()
    conn.close()
    if not rows:
        return None, None, None, None
    data = np.array(rows)
    gaze_x = data[:, 0]
    gaze_y = data[:, 1]
    timestamps = data[:, 2]
    scroll_pos = data[:, 3]
    return gaze_x, gaze_y, timestamps, scroll_pos


def apply_scroll_adjustment(gaze_x, gaze_y, scroll_pos, screen_w=SCREEN_W, screen_h=SCREEN_H):
    """
    Convert normalized gaze coordinates to pixel coordinates with scroll adjustment.
    
    Args:
        gaze_x, gaze_y: Normalized coordinates (0-1)
        scroll_pos: Scroll position in pixels
        screen_w, screen_h: Screen resolution
    
    Returns:
        x_px, y_px: Pixel coordinates adjusted for scroll
    """
    x_px = gaze_x * screen_w
    y_px = gaze_y * screen_h + scroll_pos
    return x_px, y_px


def detect_fixations(gaze_x, gaze_y, timestamps,
                     dispersion_thresh=0.02, min_duration_us=100_000):
    """I-DT fixation detection (dispersion-threshold identification).

    Args:
        gaze_x, gaze_y: normalised 0-1 gaze coordinates.
        timestamps: device timestamps in microseconds.
        dispersion_thresh: max spread (in normalised coords) for a fixation.
        min_duration_us: minimum fixation duration in microseconds.

    Returns:
        List of dicts with keys: x, y, duration_ms, start_idx, end_idx.
    """
    fixations = []
    n = len(gaze_x)
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            window_x = gaze_x[i:j + 1]
            window_y = gaze_y[i:j + 1]
            dispersion = (window_x.max() - window_x.min()) + \
                         (window_y.max() - window_y.min())
            if dispersion > dispersion_thresh:
                break
            j += 1
        duration_us = timestamps[j - 1] - timestamps[i]
        if duration_us >= min_duration_us and j - i >= 3:
            fixations.append({
                'x': float(np.mean(gaze_x[i:j])),
                'y': float(np.mean(gaze_y[i:j])),
                'duration_ms': duration_us / 1000.0,
                'start_idx': i,
                'end_idx': j - 1,
            })
            i = j
        else:
            i += 1
    return fixations


def session_label(session_row):
    """Return (tos_label, cond_label, user_label) from a session row."""
    session_id, tos_id, condition, user_name, total, valid = session_row
    return (
        tos_id or "unknown",
        condition or "unknown",
        user_name or "anonymous",
    )


def get_screenshot_path(condition_group):
    """Return path to a document screenshot for the given condition, or None."""
    for ext in ('png', 'jpg', 'jpeg'):
        path = SCREENSHOTS_DIR / f"screenshot_{condition_group}.{ext}"
        if path.exists():
            return path
    return None
