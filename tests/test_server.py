import json
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from server import app, apply_proxy_to_openapi
from urllib.parse import unquote

client = TestClient(app)

def test_proxy_invalid_url():
    # Tests error when passing an invalid URL
    response = client.get("/proxy", params={"url": "http://invalid-url"})
    assert response.status_code == 500
    assert "Failed to fetch OpenAPI document" in response.text

def test_docs_returns_html():
    # Tests if the main route returns HTML
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_proxy_with_headers():
    url = "http://example.com/openapi.json"
    headers_dict = {"Authorization": "Bearer token123"}
    headers_encoded = json.dumps(headers_dict)  # The endpoint expects headers already in JSON

    mock_response = MagicMock()
    mock_response.content = b'{"openapi": "3.0.0"}'
    mock_response.text = '{"openapi": "3.0.0"}'
    mock_response.headers = {"content-type": "application/json"}

    with patch("server.requests.get", return_value=mock_response) as mock_get:
        response = client.get("/proxy", params={"url": url, "headers": headers_encoded})
        assert response.status_code == 200
        assert response.json() == {"openapi": "3.0.0"}
        mock_get.assert_called_once()
        # Checks if the headers were passed correctly
        called_headers = mock_get.call_args[1]["headers"]
        assert called_headers == headers_dict

def test_proxy_yaml_response():
    url = "http://example.com/openapi.yaml"
    headers_dict = {"Authorization": "Bearer token123"}
    headers_json = json.dumps(headers_dict)

    yaml_content = """
openapi: 3.0.0
info:
  title: API Teste
  version: "1.0"
paths: {}
"""
    mock_response = MagicMock()
    mock_response.content = yaml_content.encode("utf-8")
    mock_response.text = yaml_content
    mock_response.headers = {"content-type": "application/yaml"}

    with patch("server.requests.get", return_value=mock_response) as mock_get:
        response = client.get("/proxy", params={"url": url, "headers": headers_json})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/yaml")
        assert "openapi: 3.0.0" in response.text
        mock_get.assert_called_once()
        called_headers = mock_get.call_args[1]["headers"]
        assert called_headers == headers_dict

def test_docs_file_not_found(monkeypatch):
    # Simulates FileNotFoundError when opening the file
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/")
        assert response.status_code == 200
        # Should contain the default aggregator name
        assert "Swagger Aggregator" in response.text

def test_docs_json_decode_error(monkeypatch):
    # Simulates invalid JSON error when opening the file
    m = mock_open(read_data="not a json")
    with patch("builtins.open", m):
        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            response = client.get("/")
            assert response.status_code == 200
            assert "Swagger Aggregator" in response.text

def test_config_json_decode_error():
    # Simulates invalid JSON error when opening the file
    m = mock_open(read_data="not a json")
    with patch("builtins.open", m):
        with patch("json.load", side_effect=Exception("invalid json")):
            response = client.get("/config")
            assert response.status_code == 200

def test_apply_proxy_to_openapi_with_http():
    url = "http://example.com/openapi.json"
    header = {"Authorization": "Bearer token"}
    result = apply_proxy_to_openapi(url, header)
    assert result.startswith("/proxy?url=http://example.com/openapi.json")
    assert "headers=" in result
    headers_param = result.split("headers=")[1]
    decoded = json.loads(unquote(headers_param))  # Fixed here!
    assert decoded == header

def test_apply_proxy_to_openapi_with_http_and_headers():
    url = "http://example.com/openapi.json"
    header = {"Authorization": "Bearer token"}
    result = apply_proxy_to_openapi(url, header)
    assert result.startswith("/proxy?url=http://example.com/openapi.json")
    assert "headers=" in result
    # Decodes and checks the header
    headers_param = result.split("headers=")[1]
    decoded = json.loads(unquote(headers_param))
    assert decoded == header

def test_apply_proxy_to_openapi_with_http_no_headers():
    url = "http://example.com/openapi.json"
    result = apply_proxy_to_openapi(url)
    assert result == f"/proxy?url={url}"

def test_apply_proxy_to_openapi_with_non_http_url():
    url = "/local/openapi.json"
    result = apply_proxy_to_openapi(url)
    assert result == url

def test_apply_proxy_to_openapi_with_empty_header():
    url = "http://example.com/openapi.json"
    result = apply_proxy_to_openapi(url, {})
    # Should not add headers if the dict is empty
    assert result == f"/proxy?url={url}"

def test_apply_proxy_to_openapi_with_special_characters_in_header():
    url = "http://example.com/openapi.json"
    header = {"X-Test": "çãõ@#%&"}
    result = apply_proxy_to_openapi(url, header)
    headers_param = result.split("headers=")[1]
    decoded = json.loads(unquote(headers_param))
    assert decoded == header
