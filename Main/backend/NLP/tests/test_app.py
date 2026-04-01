"""
Tests for the FastAPI app endpoints (app.py).

Heavy dependencies (eye tracker DLL, ML models) are avoided:
- EyeTrackingService.__init__ only sets attributes — no DLL load at import.
- analyse_text is mocked for /summarize endpoint tests.
- All database operations go to an isolated temp SQLite file.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import database


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    """Redirect all database calls to a temporary file for the duration of each test."""
    tmp_db = tmp_path / "test_app.db"
    monkeypatch.setattr(database, "DB_PATH", tmp_db)
    database.init_database()
    yield tmp_db


@pytest.fixture
def client(temp_database):
    from app import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _base_metrics(user="TestUser", session_id="sess-001"):
    return {
        "userId": user,
        "sessionId": session_id,
        "tosId": "plain-tos-001",
        "tosTitle": "E-Commerce ToS",
        "conditionGroup": "control",
        "tosLength": 5000,
        "timeStarted": "2026-01-01T10:00:00",
        "didReadComplete": True,
        "maxScrollDepth": 1.0,
        "scrollBehavior": "linear",
        "summaryGenerated": False,
    }


# ---------------------------------------------------------------------------
# Root & health
# ---------------------------------------------------------------------------

class TestRootAndHealth:
    def test_root_returns_ok(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_root_returns_version(self, client):
        data = client.get("/").json()
        assert "version" in data

    def test_health_check_returns_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# GET /api/tos/{filename}
# ---------------------------------------------------------------------------

class TestTosFileEndpoint:
    def test_disallowed_filename_returns_404(self, client):
        response = client.get("/api/tos/malicious_file")
        assert response.status_code == 404

    def test_path_traversal_blocked(self, client):
        # FastAPI/starlette rejects path-parameter traversal automatically
        response = client.get("/api/tos/../../../../etc/passwd")
        assert response.status_code in (404, 422)

    def test_allowed_name_file_missing_returns_404(self, client):
        # The file is in ALLOWED_TOS_FILES but may not exist on CI disk
        # Either 200 (file found) or 404 (file not present) is acceptable
        response = client.get("/api/tos/ecommerce_tos")
        assert response.status_code in (200, 404)

    def test_valid_response_is_plain_text(self, client):
        response = client.get("/api/tos/ecommerce_tos")
        if response.status_code == 200:
            assert "text/plain" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# POST /api/users  &  GET /api/users/{user_name}
# ---------------------------------------------------------------------------

class TestUserEndpoints:
    def test_create_user_success(self, client):
        response = client.post("/api/users", json={"name": "Alice"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice"
        assert "userId" in data

    def test_create_user_returns_message(self, client):
        data = client.post("/api/users", json={"name": "Bob"}).json()
        assert "message" in data

    def test_duplicate_user_returns_400(self, client):
        client.post("/api/users", json={"name": "Carol"})
        response = client.post("/api/users", json={"name": "Carol"})
        assert response.status_code == 400

    def test_get_existing_user(self, client):
        client.post("/api/users", json={"name": "Dave"})
        response = client.get("/api/users/Dave")
        assert response.status_code == 200
        assert response.json()["name"] == "Dave"

    def test_get_nonexistent_user_returns_404(self, client):
        response = client.get("/api/users/Nobody")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/metrics  &  GET /api/metrics/user/{user_name}
# ---------------------------------------------------------------------------

class TestMetricsEndpoints:
    def test_save_metrics_success(self, client):
        client.post("/api/users", json={"name": "TestUser"})
        response = client.post("/api/metrics", json=_base_metrics())
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_save_metrics_nonexistent_user_returns_500(self, client):
        response = client.post("/api/metrics", json=_base_metrics(user="Ghost"))
        assert response.status_code == 500

    def test_get_user_metrics(self, client):
        client.post("/api/users", json={"name": "TestUser"})
        client.post("/api/metrics", json=_base_metrics())
        response = client.get("/api/metrics/user/TestUser")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert data["total_sessions"] == 1

    def test_get_metrics_nonexistent_user_returns_404(self, client):
        response = client.get("/api/metrics/user/Nobody")
        assert response.status_code == 404

    def test_session_id_in_saved_response(self, client):
        client.post("/api/users", json={"name": "TestUser"})
        response = client.post("/api/metrics", json=_base_metrics())
        assert response.json()["sessionId"] == "sess-001"


# ---------------------------------------------------------------------------
# POST /summarize
# ---------------------------------------------------------------------------

_MOCK_ANALYSIS = {
    "bullets": ["Key point one.", "Key point two."],
    "keywords": ["data sharing", "arbitration"],
    "detected_clauses": {},
    "grouped_clauses": {},
    "risk": {"normalized_percent": 30, "raw_total": 10, "per_category": {}},
    "affects_user": [],
    "abstractive": "",
    "sections": [],
}


class TestSummarizeEndpoint:
    def test_valid_text_returns_200(self, client):
        with patch("app.analyse_text", return_value=_MOCK_ANALYSIS):
            response = client.post(
                "/summarize",
                json={"text": "A" * 100, "num_sentences": 3},
            )
        assert response.status_code == 200

    def test_response_contains_bullets(self, client):
        with patch("app.analyse_text", return_value=_MOCK_ANALYSIS):
            data = client.post(
                "/summarize",
                json={"text": "A" * 100, "num_sentences": 3},
            ).json()
        assert "bullets" in data

    def test_text_too_short_returns_422(self, client):
        response = client.post(
            "/summarize",
            json={"text": "Short", "num_sentences": 3},
        )
        assert response.status_code == 422

    def test_num_sentences_out_of_range_returns_422(self, client):
        response = client.post(
            "/summarize",
            json={"text": "A" * 100, "num_sentences": 50},
        )
        assert response.status_code == 422

    def test_text_too_long_returns_422(self, client):
        response = client.post(
            "/summarize",
            json={"text": "A" * 500_001, "num_sentences": 3},
        )
        assert response.status_code == 422

    def test_abstractive_flag_passed_through(self, client):
        with patch("app.analyse_text", return_value=_MOCK_ANALYSIS) as mock_fn:
            client.post(
                "/summarize",
                json={"text": "A" * 100, "num_sentences": 3, "abstractive": True},
            )
        mock_fn.assert_called_once()
        _, kwargs = mock_fn.call_args
        assert kwargs.get("do_abstractive") is True


# ---------------------------------------------------------------------------
# GET /api/stats
# ---------------------------------------------------------------------------

class TestStatsEndpoint:
    def test_returns_200(self, client):
        assert client.get("/api/stats").status_code == 200

    def test_contains_count_fields(self, client):
        data = client.get("/api/stats").json()
        for field in ("total_users", "total_sessions", "total_scroll_events", "total_clause_clicks"):
            assert field in data

    def test_counts_zero_initially(self, client):
        data = client.get("/api/stats").json()
        assert data["total_users"] == 0
        assert data["total_sessions"] == 0

    def test_user_count_increments(self, client):
        client.post("/api/users", json={"name": "Alice"})
        client.post("/api/users", json={"name": "Bob"})
        data = client.get("/api/stats").json()
        assert data["total_users"] == 2


# ---------------------------------------------------------------------------
# GET /api/export/csv
# ---------------------------------------------------------------------------

class TestExportCsvEndpoint:
    def test_no_data_returns_404(self, client):
        assert client.get("/api/export/csv").status_code == 404

    def test_with_data_returns_csv(self, client):
        client.post("/api/users", json={"name": "ExportUser"})
        client.post("/api/metrics", json=_base_metrics(user="ExportUser", session_id="sess-exp"))
        response = client.get("/api/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_csv_has_attachment_header(self, client):
        client.post("/api/users", json={"name": "ExportUser"})
        client.post("/api/metrics", json=_base_metrics(user="ExportUser", session_id="sess-exp"))
        response = client.get("/api/export/csv")
        assert "attachment" in response.headers.get("content-disposition", "")


# ---------------------------------------------------------------------------
# POST /api/comprehension-test
# ---------------------------------------------------------------------------

class TestComprehensionTestEndpoint:
    def test_save_returns_success(self, client):
        payload = {
            "userName": "Alice",
            "timestamp": "2026-01-01T10:00:00",
            "recognitionScore": 80,
            "avgConfidence": 3.5,
            "recognitionAnswers": ["yes", "no", "unsure"],
            "confidenceAnswers": [4, 3, 2],
        }
        response = client.post("/api/comprehension-test", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_partial_payload_accepted(self, client):
        # Only mandatory fields provided; optional fields default to empty
        payload = {"userName": "Bob", "timestamp": "2026-01-01T10:00:00"}
        response = client.post("/api/comprehension-test", json=payload)
        assert response.status_code == 200
