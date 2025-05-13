from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import requests
import logging
from urllib.parse import quote, unquote

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

# static files
app.mount("/openapi", StaticFiles(directory="static/openapi"), name="openapi")

templates = Jinja2Templates(directory="templates")

fastapi_ui_html = """
<html>
<head>
    <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    <title>{{ title }}</title>
</head>
<body>
    <div id="swagger-ui"></div>

    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-standalone-preset.js"></script>

    <script>
    const ui = SwaggerUIBundle({
        urls: {{ urls | safe }},
        dom_id: "#swagger-ui",
        layout: "StandaloneLayout",
        deepLinking: true,
        showExtensions: true,
        showCommonExtensions: true,
        oauth2RedirectUrl: window.location.origin + '/oauth2-redirect',
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
        ],
    })
    </script>

</body>
</html>
"""

@app.get("/proxy", include_in_schema=False)
async def proxy(url: str, headers: str = None):
    """
    Proxy endpoint to fetch the OpenAPI JSON from a given URL.
    """
    if headers:
        response = requests.get(url, headers=json.loads(unquote(headers)))
    else:
        response = requests.get(url)
    return response.json()

def parse_headers(header_string: str) -> dict:
    headers = {}
    if not header_string:
        return headers
    for line in header_string.strip().split('\n'):
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def apply_proxy_to_openapi(openapi_url: str, header: str = None) -> str:
    """
    Apply the proxy to the OpenAPI URL.
    """
    if openapi_url.startswith("http"):
        new_url = f"/proxy?url={openapi_url}"
        if header:
            header = quote(json.dumps(header))
            new_url += f"&headers={header}"
        return new_url
    return openapi_url


@app.get("/", response_class=HTMLResponse)
async def docs(request: Request):
    try:
        with open('static/openapi/urls.json') as f:
            swaggers = json.load(f)
    except FileNotFoundError:
        swaggers = [
            {
                "url": "/openapi.json",
                "name": "Swagger Aggregator",
                "header": "",
            }
        ]
    except json.JSONDecodeError:
        swaggers = [
            {
                "url": "/openapi.json",
                "name": "Swagger Aggregator",
                "header": "",
            }
        ]

    for swagger in swaggers:
        swagger["url"] = apply_proxy_to_openapi(swagger["url"], parse_headers(swagger["header"]))

    # Renderiza o template HTML diretamente
    html = fastapi_ui_html.replace(
        "{{ urls | safe }}", json.dumps(swaggers)
    ).replace(
        "{{ title }}", os.environ.get("TITLE", "API Documentation")
    )
    return HTMLResponse(content=html)
