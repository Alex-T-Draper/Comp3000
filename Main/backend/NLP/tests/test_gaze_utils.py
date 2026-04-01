"""
Tests for gaze_utils.py — pure computation functions only.
DB-accessing functions (get_sessions, get_gaze_points) are not tested here
as they require a populated database with gaze samples.
"""
import pytest
import numpy as np

from gaze_utils import (
    apply_scroll_adjustment,
    detect_fixations,
    session_label,
    SCREEN_W,
    SCREEN_H,
)


# ---------------------------------------------------------------------------
# apply_scroll_adjustment
# ---------------------------------------------------------------------------

class TestApplyScrollAdjustment:
    def test_normalised_centre_maps_to_pixel_centre(self):
        gaze_x = np.array([0.5])
        gaze_y = np.array([0.5])
        scroll = np.array([0.0])
        x_px, y_px = apply_scroll_adjustment(gaze_x, gaze_y, scroll)
        assert x_px[0] == pytest.approx(0.5 * SCREEN_W)
        assert y_px[0] == pytest.approx(0.5 * SCREEN_H)

    def test_zero_gaze_maps_to_origin(self):
        gaze_x = np.array([0.0])
        gaze_y = np.array([0.0])
        scroll = np.array([0.0])
        x_px, y_px = apply_scroll_adjustment(gaze_x, gaze_y, scroll)
        assert x_px[0] == pytest.approx(0.0)
        assert y_px[0] == pytest.approx(0.0)

    def test_scroll_offset_added_to_y(self):
        gaze_x = np.array([0.0])
        gaze_y = np.array([0.0])
        scroll = np.array([300.0])
        _, y_px = apply_scroll_adjustment(gaze_x, gaze_y, scroll)
        assert y_px[0] == pytest.approx(300.0)

    def test_full_normalised_coords_map_to_screen_size(self):
        gaze_x = np.array([1.0])
        gaze_y = np.array([1.0])
        scroll = np.array([0.0])
        x_px, y_px = apply_scroll_adjustment(gaze_x, gaze_y, scroll)
        assert x_px[0] == pytest.approx(float(SCREEN_W))
        assert y_px[0] == pytest.approx(float(SCREEN_H))

    def test_custom_screen_dimensions(self):
        gaze_x = np.array([0.5])
        gaze_y = np.array([0.5])
        scroll = np.array([0.0])
        x_px, y_px = apply_scroll_adjustment(
            gaze_x, gaze_y, scroll, screen_w=1920, screen_h=1080
        )
        assert x_px[0] == pytest.approx(960.0)
        assert y_px[0] == pytest.approx(540.0)

    def test_multiple_points(self):
        gaze_x = np.array([0.0, 0.5, 1.0])
        gaze_y = np.array([0.0, 0.5, 1.0])
        scroll = np.array([0.0, 0.0, 0.0])
        x_px, y_px = apply_scroll_adjustment(gaze_x, gaze_y, scroll)
        assert len(x_px) == 3
        assert len(y_px) == 3


# ---------------------------------------------------------------------------
# detect_fixations
# ---------------------------------------------------------------------------

def _stable_gaze(n=20, cx=0.5, cy=0.5, jitter=0.0001, step_us=10_000):
    """Produce n gaze points tightly clustered around (cx, cy)."""
    x = np.array([cx + i * jitter for i in range(n)])
    y = np.array([cy + i * jitter for i in range(n)])
    ts = np.array([i * step_us for i in range(n)], dtype=float)
    return x, y, ts


class TestDetectFixations:
    def test_stable_gaze_produces_one_fixation(self):
        # 20 points, dispersion ≈ 0.0019 < 0.02 threshold, duration 190ms > 100ms
        x, y, ts = _stable_gaze(n=20, jitter=0.0001, step_us=10_000)
        fixations = detect_fixations(x, y, ts)
        assert len(fixations) == 1

    def test_fixation_has_required_keys(self):
        x, y, ts = _stable_gaze(n=20)
        fixations = detect_fixations(x, y, ts)
        assert len(fixations) >= 1
        f = fixations[0]
        for key in ("x", "y", "duration_ms", "start_idx", "end_idx"):
            assert key in f

    def test_fixation_duration_positive(self):
        x, y, ts = _stable_gaze(n=20, step_us=10_000)
        fixations = detect_fixations(x, y, ts)
        if fixations:
            assert fixations[0]["duration_ms"] > 0

    def test_fixation_position_within_gaze_bounds(self):
        x, y, ts = _stable_gaze(n=20, cx=0.5, cy=0.5)
        fixations = detect_fixations(x, y, ts)
        if fixations:
            f = fixations[0]
            assert 0.0 <= f["x"] <= 1.0
            assert 0.0 <= f["y"] <= 1.0

    def test_saccade_produces_no_fixation(self):
        # Points moving rapidly across screen — exceeds dispersion threshold per step
        n = 20
        x = np.linspace(0.0, 1.0, n)   # full screen sweep
        y = np.zeros(n)
        ts = np.array([i * 10_000 for i in range(n)], dtype=float)
        fixations = detect_fixations(x, y, ts)
        # Dispersion will exceed 0.02 almost immediately
        assert isinstance(fixations, list)
        # No long fixation should be detected across the full sweep
        assert len(fixations) == 0

    def test_short_duration_gaze_not_counted(self):
        # Only 3 points at 1ms each → duration = 2ms < 100ms minimum
        x, y, ts = _stable_gaze(n=3, step_us=1_000)
        fixations = detect_fixations(x, y, ts)
        assert len(fixations) == 0

    def test_returns_empty_list_for_single_point(self):
        x = np.array([0.5])
        y = np.array([0.5])
        ts = np.array([0.0])
        fixations = detect_fixations(x, y, ts)
        assert fixations == []

    def test_two_separate_fixations_detected(self):
        # First cluster at (0.2, 0.5), second cluster at (0.8, 0.5)
        n = 15
        jitter = 0.0001
        step = 10_000
        x1 = np.array([0.2 + i * jitter for i in range(n)])
        y1 = np.array([0.5 + i * jitter for i in range(n)])
        ts1 = np.array([i * step for i in range(n)], dtype=float)

        x2 = np.array([0.8 + i * jitter for i in range(n)])
        y2 = np.array([0.5 + i * jitter for i in range(n)])
        ts2 = np.array([(n + 1 + i) * step for i in range(n)], dtype=float)

        x = np.concatenate([x1, x2])
        y = np.concatenate([y1, y2])
        ts = np.concatenate([ts1, ts2])
        fixations = detect_fixations(x, y, ts)
        assert len(fixations) == 2


# ---------------------------------------------------------------------------
# session_label
# ---------------------------------------------------------------------------

class TestSessionLabel:
    def test_extracts_tos_id_condition_username(self):
        row = ("session-123", "ecommerce_tos", "control", "Alice", 100, 90)
        tos_id, condition, user_name = session_label(row)
        assert tos_id == "ecommerce_tos"
        assert condition == "control"
        assert user_name == "Alice"

    def test_none_tos_id_defaults_to_unknown(self):
        row = ("session-456", None, "ai-summary", "Bob", 50, 40)
        tos_id, condition, user_name = session_label(row)
        assert tos_id == "unknown"

    def test_none_condition_defaults_to_unknown(self):
        row = ("session-789", "socialmedia_tos", None, "Carol", 80, 75)
        tos_id, condition, user_name = session_label(row)
        assert condition == "unknown"

    def test_none_user_name_defaults_to_anonymous(self):
        row = ("session-000", "fitness_tos", "formatted", None, 60, 55)
        tos_id, condition, user_name = session_label(row)
        assert user_name == "anonymous"

    def test_all_none_metadata_returns_all_defaults(self):
        row = ("session-999", None, None, None, 10, 5)
        tos_id, condition, user_name = session_label(row)
        assert tos_id == "unknown"
        assert condition == "unknown"
        assert user_name == "anonymous"
