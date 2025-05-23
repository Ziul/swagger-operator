from unittest.mock import MagicMock, patch

import pytest
from controller import service_event

@pytest.fixture
def fake_memo():
    class Memo:
        apps = {}
    return Memo()

def make_event(path):
    return {
        'type': 'ADDED',
        'object': {
            'metadata': {
                'name': 'my-service',
                'namespace': 'default',
                'annotations': {
                    'swagger-operator-path': path,
                    'swagger-operator-name': 'my-app',
                    'swagger-operator-port': '8080',
                    'swagger-operator-header': 'X-API-KEY'
                }
            }
        }
    }

def test_path_without_slash(fake_memo):
    # Path without leading slash
    event = make_event("openapi.json")
    logger = MagicMock()
    with patch("builtins.open"), patch("json.dump"):
        service_event(event, fake_memo, logger)
    key = "default.my-app"
    assert key in fake_memo.apps
    # The final path should contain the original path
    assert fake_memo.apps[key]['url'].endswith("/openapi.json")

def test_path_with_slash(fake_memo):
    # Path with leading slash
    event = make_event("/openapi.json")
    logger = MagicMock()
    with patch("builtins.open"), patch("json.dump"):
        service_event(event, fake_memo, logger)
    key = "default.my-app"
    assert key in fake_memo.apps
    assert fake_memo.apps[key]['url'].endswith("/openapi.json")

def test_path_with_host(fake_memo):
    # Path with host
    event = make_event("http://myhost/openapi.json")
    logger = MagicMock()
    with patch("builtins.open"), patch("json.dump"):
        service_event(event, fake_memo, logger)
    key = "default.my-app"
    assert key in fake_memo.apps
    # The host should be preserved
    assert fake_memo.apps[key]['url'].startswith("http://myhost")

def test_missing_annotation(fake_memo):
    # Missing annotation
    event = make_event("/openapi.json")
    del event['object']['metadata']['annotations']['swagger-operator-path']
    logger = MagicMock()
    with patch("builtins.open"), patch("json.dump"):
        try:
            service_event(event, fake_memo, logger)
            assert False, "Should raise KeyError"
        except KeyError:
            pass

def test_service_event_deleted(fake_memo):
    # Pre-add an app to memo
    fake_memo.apps["default.my-app"] = {
        "url": "http://dummy",
        "name": "my-app",
        "header": "X-API-KEY"
    }
    event = {
        'type': 'DELETED',
        'object': {
            'metadata': {
                'name': 'my-service',
                'namespace': 'default',
                'annotations': {
                    'swagger-operator-path': '/openapi.json',
                    'swagger-operator-name': 'my-app',
                    'swagger-operator-port': '8080',
                    'swagger-operator-header': 'X-API-KEY'
                }
            }
        }
    }
    logger = MagicMock()
    with patch("builtins.open"), patch("json.dump"):
        service_event(event, fake_memo, logger)
    # Should remove the app from memo
    assert "default.my-app" not in fake_memo.apps