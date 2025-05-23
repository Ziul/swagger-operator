import json
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from server import app

import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def set_proxy_timeout(monkeypatch):
    monkeypatch.setenv("PROXY_TIMEOUT", "1")

def test_services_invalid_name():
    # Tests error when passing an invalid service name
    response = client.get("/services/i-dont-exist")
    assert response.status_code == 404
    assert "Service not found" in response.text

def test_services_json_response():
    # Tests if JSON is returned correctly
    mock_response = MagicMock()
    mock_response.content = b'{"openapi": "3.0.0"}'
    mock_response.headers = {"content-type": "application/json"}

    with patch("server.requests.get", return_value=mock_response):
        response = client.get("/services/default.nginx")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == {"openapi": "3.0.0"}

def test_services_yaml_response():
    # Tests if YAML is returned correctly
    yaml_content = """
openapi: 3.0.0
info:
  title: API Teste
  version: "1.0"
paths: {}
"""
    mock_response = MagicMock()
    mock_response.content = yaml_content.encode("utf-8")
    mock_response.headers = {"content-type": "application/yaml"}

    with patch("server.requests.get", return_value=mock_response):
        response = client.get("/services/default.timeout")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/yaml")
        assert "openapi: 3.0.0" in response.text

def test_services_unsupported_content_type():
    # Tests error for unsupported content-type
    mock_response = MagicMock()
    mock_response.content = b"not supported"
    mock_response.headers = {"content-type": "text/plain"}

    with patch("server.requests.get", return_value=mock_response):
        response = client.get("/services/default.nginx")
        assert response.status_code == 400
        assert "Unsupported content type" in response.text

def test_docs_returns_html():
    # Tests if the main route returns HTML
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_docs_file_not_found(monkeypatch):
    # Simulates FileNotFoundError when opening the file
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/")
        assert response.status_code == 500
        assert "Error loading services file" in response.text

def test_docs_json_decode_error(monkeypatch):
    # Simulates invalid JSON error when opening the file
    m = mock_open(read_data="not a json")
    with patch("builtins.open", m):
        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            response = client.get("/")
            assert response.status_code == 500
            assert "Error loading services file" in response.text

def test_config_json_decode_error():
    # Simulates invalid JSON error when opening the config file
    m = mock_open(read_data="not a json")
    with patch("builtins.open", m):
        with patch("json.load", side_effect=Exception("invalid json")):
            response = client.get("/config")
            assert response.status_code == 200
