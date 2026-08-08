import io
import json
import pytest
from unittest.mock import MagicMock
from urllib.parse import urlparse
from src.api_server import DashboardAPIHandler


class DummyRequest:
    def __init__(self, path):
        self.path = path

    def makefile(self, *args, **kwargs):
        return io.BytesIO(b"")


def test_api_health_endpoint():
    handler = DashboardAPIHandler.__new__(DashboardAPIHandler)
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    parsed = urlparse("/api/health")
    handler.handle_api("/api/health", parsed)

    output = handler.wfile.getvalue().decode("utf-8")
    data = json.loads(output)
    assert data["status"] == "online"
    assert "api_version" in data


def test_api_summary_endpoint():
    handler = DashboardAPIHandler.__new__(DashboardAPIHandler)
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    parsed = urlparse("/api/summary")
    handler.handle_api("/api/summary", parsed)

    output = handler.wfile.getvalue().decode("utf-8")
    data = json.loads(output)
    assert "table_counts" in data
    assert "status" in data


def test_api_dupont_endpoint():
    handler = DashboardAPIHandler.__new__(DashboardAPIHandler)
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    parsed = urlparse("/api/analytics/dupont?company_id=COMP01")
    handler.handle_api("/api/analytics/dupont", parsed)

    output = handler.wfile.getvalue().decode("utf-8")
    data = json.loads(output)
    assert "company_id" in data
    assert "history" in data


def test_api_screener_rank_endpoint():
    handler = DashboardAPIHandler.__new__(DashboardAPIHandler)
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    parsed = urlparse("/api/screener/rank")
    handler.handle_api("/api/screener/rank", parsed)

    output = handler.wfile.getvalue().decode("utf-8")
    data = json.loads(output)
    assert isinstance(data, list)


def test_api_risk_endpoint():
    handler = DashboardAPIHandler.__new__(DashboardAPIHandler)
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    parsed = urlparse("/api/analytics/risk?ticker=COMP01")
    handler.handle_api("/api/analytics/risk", parsed)

    output = handler.wfile.getvalue().decode("utf-8")
    data = json.loads(output)
    assert data["ticker"] == "COMP01"
    assert "risk_metrics" in data
