from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app import logging_config
from app.main import agent, app, unhandled_exception_handler
from app.middleware import CorrelationIdMiddleware


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]


def test_middleware_generates_distinct_correlation_ids_and_timing_header() -> None:
    with TestClient(app) as client:
        first = client.get("/health")
        second = client.get("/health")

    first_id = first.headers["x-request-id"]
    second_id = second.headers["x-request-id"]
    assert re.fullmatch(r"req-[0-9a-f]{8}", first_id)
    assert re.fullmatch(r"req-[0-9a-f]{8}", second_id)
    assert first_id != second_id
    assert float(first.headers["x-response-time-ms"]) >= 0


def test_middleware_preserves_non_empty_client_correlation_id() -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"x-request-id": "client-request-42"})

    assert response.headers["x-request-id"] == "client-request-42"


def test_middleware_replaces_blank_client_correlation_id() -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"x-request-id": "   "})

    assert re.fullmatch(r"req-[0-9a-f]{8}", response.headers["x-request-id"])


def test_chat_logs_share_client_correlation_id(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"x-request-id": "client-request-99"},
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    request_events = [
        event for event in events if event["event"] in {"request_received", "response_sent"}
    ]
    assert {event["correlation_id"] for event in request_events} == {"client-request-99"}
    assert all("user_id" not in event for event in request_events)


def test_chat_failure_is_safe_and_keeps_correlation_id(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    secret_detail = "private failure detail"

    def fail_agent(**_kwargs):
        raise RuntimeError(secret_detail)

    monkeypatch.setattr(agent, "run", fail_agent)
    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"x-request-id": "client-error-01"},
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Trigger a controlled failure",
            },
        )

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "client-error-01"
    assert secret_detail not in response.text
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    failure = next(event for event in events if event["event"] == "request_failed")
    assert failure["correlation_id"] == "client-error-01"
    assert failure["error_type"] == "RuntimeError"


def test_global_exception_handler_returns_safe_correlated_response(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    test_app = FastAPI()
    test_app.add_middleware(CorrelationIdMiddleware)
    test_app.add_exception_handler(Exception, unhandled_exception_handler)

    @test_app.get("/explode")
    async def explode() -> JSONResponse:
        raise ValueError("sensitive internal detail")

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/explode", headers={"x-request-id": "global-error-01"})

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "global-error-01"
    assert float(response.headers["x-response-time-ms"]) >= 0
    assert response.json() == {
        "detail": "Internal Server Error",
        "correlation_id": "global-error-01",
    }
    assert "sensitive internal detail" not in response.text
