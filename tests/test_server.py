import json
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from server import app, parse_headers

import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def set_proxy_timeout(monkeypatch):
    monkeypatch.setenv("PROXY_TIMEOUT", "1")

def test_services_invalid_name():
    # Tests error when passing an invalid service name
    services_dict = {
        "default.nginx": {
            "url": "http://nginx",
            "name": "nginx",
            "header": ""
        }
    }
    m = mock_open(read_data=json.dumps(services_dict))
    with patch("builtins.open", m):
        response = client.get("/services/i-dont-exist")
        assert response.status_code == 404
        assert "Service not found" in response.text

def test_services_json_response():
    # Tests if JSON is returned correctly
    mock_response = MagicMock()
    mock_response.content = b'{"openapi": "3.0.0"}'
    mock_response.headers = {"content-type": "application/json"}

    services_dict = {
        "default.nginx": {
            "url": "http://nginx",
            "name": "nginx",
            "header": ""
        }
    }
    m = mock_open(read_data=json.dumps(services_dict))
    with patch("builtins.open", m):
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

    services_dict = {
        "default.timeout": {
            "url": "http://timeout",
            "name": "timeout",
            "header": ""
        }
    }
    m = mock_open(read_data=json.dumps(services_dict))
    with patch("builtins.open", m):
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

    services_dict = {
        "default.nginx": {
            "url": "http://nginx",
            "name": "nginx",
            "header": ""
        }
    }
    m = mock_open(read_data=json.dumps(services_dict))
    with patch("builtins.open", m):
        with patch("server.requests.get", return_value=mock_response):
            response = client.get("/services/default.nginx")
            assert response.status_code == 400
            assert "Unsupported content type" in response.text

def test_docs_returns_html():
    # Tests if the main route returns HTML
    services_dict = {
        "default.nginx": {
            "url": "http://nginx",
            "name": "nginx",
            "header": ""
        }
    }
    m = mock_open(read_data=json.dumps(services_dict))
    with patch("builtins.open", m):
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

def test_parse_headers_empty():
    # Tests parse_headers with empty input
    assert parse_headers("") == {}
    assert parse_headers(None) == {}

def test_parse_headers_valid():
    # Tests parse_headers with valid headers string
    header_string = "Authorization: Bearer token\nX-Test: value"
    expected = {"Authorization": "Bearer token", "X-Test": "value"}
    assert parse_headers(header_string) == expected

def test_parse_headers_invalid_lines():
    # Tests parse_headers with lines without colon
    header_string = "InvalidLine\nKey: Value"
    expected = {"Key": "Value"}
    assert parse_headers(header_string) == expected

def test_index_invalid_template():
    # Tests if the main route returns 400 for invalid template
    services_dict = {
        "default.nginx": {
            "url": "http://nginx",
            "name": "nginx",
            "header": ""
        }
    }
    m = mock_open(read_data=json.dumps(services_dict))
    with patch("builtins.open", m):
        response = client.get("/?template=invalid")
        assert response.status_code == 400
        assert "Invalid template" in response.text
