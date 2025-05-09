from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os

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
            }
        ]
    except json.JSONDecodeError:
        swaggers = [
            {
                "url": "/openapi.json",
                "name": "Swagger Aggregator",
            }
        ]
    # Renderiza o template HTML diretamente
    html = fastapi_ui_html.replace(
        "{{ urls | safe }}", json.dumps(swaggers)
    ).replace(
        "{{ title }}", os.environ.get("TITLE", "API Documentation")
    )
    return HTMLResponse(content=html)
