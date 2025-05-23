import json
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from server import app, apply_proxy_to_openapi
from urllib.parse import unquote

import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def set_proxy_timeout(monkeypatch):
    monkeypatch.setenv("PROXY_TIMEOUT", "1")

def test_services_invalid_name():
    # Testa erro ao passar um nome inválido
    response = client.get("/services/inexistente")
    assert response.status_code == 404
    assert "Service not found" in response.text

def test_services_json_response():
    # Testa se retorna JSON corretamente
    mock_response = MagicMock()
    mock_response.content = b'{"openapi": "3.0.0"}'
    mock_response.headers = {"content-type": "application/json"}

    with patch("server.requests.get", return_value=mock_response):
        response = client.get("/services/default.nginx")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == {"openapi": "3.0.0"}

def test_services_yaml_response():
    # Testa se retorna YAML corretamente
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
    # Testa erro para content-type não suportado
    mock_response = MagicMock()
    mock_response.content = b"not supported"
    mock_response.headers = {"content-type": "text/plain"}

    with patch("server.requests.get", return_value=mock_response):
        response = client.get("/services/default.nginx")
        assert response.status_code == 400
        assert "Unsupported content type" in response.text

def test_docs_returns_html():
    # Testa se a rota principal retorna HTML
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_docs_file_not_found(monkeypatch):
    # Simula FileNotFoundError ao abrir o arquivo
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/")
        assert response.status_code == 500
        assert "Error loading services file" in response.text

def test_docs_json_decode_error(monkeypatch):
    # Simula erro de JSON inválido ao abrir o arquivo
    m = mock_open(read_data="not a json")
    with patch("builtins.open", m):
        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            response = client.get("/")
            assert response.status_code == 500
            assert "Error loading services file" in response.text

def test_config_json_decode_error():
    # Simula erro de JSON inválido ao abrir o arquivo de config
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
    assert result == f"/proxy?url={url}"

def test_apply_proxy_to_openapi_with_special_characters_in_header():
    url = "http://example.com/openapi.json"
    header = {"X-Test": "çãõ@#%&"}
    result = apply_proxy_to_openapi(url, header)
    headers_param = result.split("headers=")[1]
    decoded = json.loads(unquote(headers_param))
    assert decoded == header
