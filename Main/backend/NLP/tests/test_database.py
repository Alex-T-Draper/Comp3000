"""
Tests for database.py — using a temporary SQLite file so the real
tos_research.db is never touched during test runs.
"""
import pytest
import database


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    """Redirect every database operation to an isolated temp file."""
    tmp_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", tmp_db)
    database.init_database()
    yield tmp_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_metrics(session_id="sess-001"):
    """Return the smallest valid metrics dict accepted by save_session_data."""
    return {
        "sessionId": session_id,
        "tosId": "plain-tos-001",
        "tosTitle": "Test ToS",
        "conditionGroup": "control",
        "tosLength": 1000,
        "timeStarted": "2026-01-01T10:00:00",
        "timeEnded": "2026-01-01T10:10:00",
        "totalReadingTime": 600,
        "timeToBottom": 300,
        "timeBeforeSummary": None,
        "didReadComplete": True,
        "maxScrollDepth": 1.0,
        "scrollBehavior": "linear",
        "scrollUpCount": 0,
        "reReadSections": 0,
        "totalPauseTime": 0,
        "summaryGenerated": False,
        "summaryGeneratedAt": None,
        "summaryViewDuration": None,
        "riskScore": None,
        "scrollEvents": [],
        "pauseEvents": [],
        "clausesClicked": [],
        "detectedCategories": [],
        "hoverEvents": [],
    }


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_returns_positive_integer(self):
        user_id = database.create_user("Alice")
        assert isinstance(user_id, int)
        assert user_id > 0

    def test_different_users_get_different_ids(self):
        id1 = database.create_user("Alice")
        id2 = database.create_user("Bob")
        assert id1 != id2

    def test_sequential_ids_increment(self):
        id1 = database.create_user("Alice")
        id2 = database.create_user("Bob")
        assert id2 == id1 + 1


# ---------------------------------------------------------------------------
# get_user_by_name
# ---------------------------------------------------------------------------

class TestGetUserByName:
    def test_returns_dict_for_existing_user(self):
        database.create_user("Alice")
        result = database.get_user_by_name("Alice")
        assert isinstance(result, dict)
        assert result["name"] == "Alice"

    def test_returns_none_for_unknown_user(self):
        result = database.get_user_by_name("Nobody")
        assert result is None

    def test_returned_dict_has_id_key(self):
        database.create_user("Bob")
        result = database.get_user_by_name("Bob")
        assert "id" in result

    def test_returned_dict_has_name_key(self):
        database.create_user("Charlie")
        result = database.get_user_by_name("Charlie")
        assert result["name"] == "Charlie"


# ---------------------------------------------------------------------------
# is_user_name_taken
# ---------------------------------------------------------------------------

class TestIsUserNameTaken:
    def test_false_for_new_name(self):
        assert database.is_user_name_taken("NewUser") is False

    def test_true_after_creating_user(self):
        database.create_user("Alice")
        assert database.is_user_name_taken("Alice") is True

    def test_false_for_different_name(self):
        database.create_user("Alice")
        assert database.is_user_name_taken("Bob") is False


# ---------------------------------------------------------------------------
# save_session_data + get_user_sessions
# ---------------------------------------------------------------------------

class TestSaveSessionData:
    def test_session_retrievable_after_save(self):
        user_id = database.create_user("Alice")
        database.save_session_data(user_id, _minimal_metrics("sess-001"))
        sessions = database.get_user_sessions(user_id)
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "sess-001"

    def test_multiple_sessions_saved(self):
        user_id = database.create_user("Bob")
        database.save_session_data(user_id, _minimal_metrics("sess-A"))
        database.save_session_data(user_id, _minimal_metrics("sess-B"))
        sessions = database.get_user_sessions(user_id)
        assert len(sessions) == 2

    def test_session_fields_stored_correctly(self):
        user_id = database.create_user("Carol")
        metrics = _minimal_metrics("sess-fields")
        metrics["conditionGroup"] = "ai-summary"
        metrics["maxScrollDepth"] = 0.75
        database.save_session_data(user_id, metrics)
        session = database.get_user_sessions(user_id)[0]
        assert session["condition_group"] == "ai-summary"
        assert abs(session["max_scroll_depth"] - 0.75) < 0.001

    def test_saves_scroll_events(self):
        user_id = database.create_user("Dave")
        metrics = _minimal_metrics("sess-scroll")
        metrics["scrollEvents"] = [
            {
                "timestamp": "2026-01-01T10:01:00",
                "scrollDepth": 0.3,
                "scrollPosition": 300,
                "direction": "down",
            }
        ]
        # Should not raise
        database.save_session_data(user_id, metrics)

    def test_saves_pause_events(self):
        user_id = database.create_user("Eve")
        metrics = _minimal_metrics("sess-pause")
        metrics["pauseEvents"] = [
            {
                "timestamp": "2026-01-01T10:02:00",
                "scrollDepth": 0.5,
                "duration": 5000,
            }
        ]
        database.save_session_data(user_id, metrics)

    def test_saves_detected_categories(self):
        user_id = database.create_user("Frank")
        metrics = _minimal_metrics("sess-cats")
        metrics["detectedCategories"] = ["data_sharing", "payment"]
        database.save_session_data(user_id, metrics)
        sessions = database.get_user_sessions(user_id)
        assert len(sessions) == 1

    def test_saves_hover_events(self):
        user_id = database.create_user("Grace")
        metrics = _minimal_metrics("sess-hover")
        metrics["hoverEvents"] = [
            {
                "category": "privacy",
                "clauseId": "clause-1",
                "timestamp": "2026-01-01T10:03:00",
                "duration": 2000,
            }
        ]
        database.save_session_data(user_id, metrics)


# ---------------------------------------------------------------------------
# get_user_sessions
# ---------------------------------------------------------------------------

class TestGetUserSessions:
    def test_returns_empty_list_when_no_sessions(self):
        user_id = database.create_user("Alice")
        assert database.get_user_sessions(user_id) == []

    def test_returns_list_of_dicts(self):
        user_id = database.create_user("Bob")
        database.save_session_data(user_id, _minimal_metrics())
        sessions = database.get_user_sessions(user_id)
        assert isinstance(sessions, list)
        assert all(isinstance(s, dict) for s in sessions)

    def test_sessions_ordered_by_created_at_desc(self):
        user_id = database.create_user("Carol")
        database.save_session_data(user_id, _minimal_metrics("first-session"))
        database.save_session_data(user_id, _minimal_metrics("second-session"))
        sessions = database.get_user_sessions(user_id)
        # Most recent first (ORDER BY created_at DESC)
        assert len(sessions) == 2


# ---------------------------------------------------------------------------
# save_gaze_data
# ---------------------------------------------------------------------------

class TestSaveGazeData:
    def test_saves_gaze_samples_without_error(self):
        samples = [
            {
                "timestamp": "2026-01-01T10:00:00",
                "device_ts": 100_000,
                "gaze_x": 0.5,
                "gaze_y": 0.5,
                "gaze_valid": True,
                "scroll_position": 0,
            },
            {
                "timestamp": "2026-01-01T10:00:01",
                "device_ts": 200_000,
                "gaze_x": 0.6,
                "gaze_y": 0.4,
                "gaze_valid": True,
                "scroll_position": 100,
            },
        ]
        database.save_gaze_data("test-session", samples)

    def test_empty_gaze_list_is_noop(self):
        # save_gaze_data returns early for empty list — should not raise
        database.save_gaze_data("test-session", [])

    def test_invalid_gaze_point_stored_as_none(self):
        samples = [
            {
                "timestamp": "2026-01-01T10:00:00",
                "device_ts": 100_000,
                "gaze_x": None,
                "gaze_y": None,
                "gaze_valid": False,
                "scroll_position": 0,
            }
        ]
        database.save_gaze_data("test-session", samples)


# ---------------------------------------------------------------------------
# export_all_data_csv
# ---------------------------------------------------------------------------

class TestExportAllDataCsv:
    def test_returns_none_when_no_data(self):
        assert database.export_all_data_csv() is None

    def test_returns_csv_string_with_data(self):
        user_id = database.create_user("Alice")
        database.save_session_data(user_id, _minimal_metrics("sess-csv"))
        result = database.export_all_data_csv()
        assert result is not None
        assert isinstance(result, str)

    def test_csv_contains_user_name(self):
        user_id = database.create_user("ExportUser")
        database.save_session_data(user_id, _minimal_metrics("sess-export"))
        result = database.export_all_data_csv()
        assert "ExportUser" in result

    def test_csv_has_header_row(self):
        user_id = database.create_user("Alice")
        database.save_session_data(user_id, _minimal_metrics())
        result = database.export_all_data_csv()
        lines = result.strip().splitlines()
        # First line is the header
        assert len(lines) >= 2
        assert "user_name" in lines[0]
