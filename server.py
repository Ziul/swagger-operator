from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import requests
import logging
import yaml
from urllib.parse import quote, unquote
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

# static files
app.mount("/openapi", StaticFiles(directory="static/openapi"), name="openapi")
# templates
templates = Jinja2Templates(directory="templates")

ENABLE_OIDC = os.environ.get("ENABLE_OIDC", "false").lower() == "true"

if ENABLE_OIDC:
    config = Config('.env')  # ou use variáveis de ambiente diretamente
    oauth = OAuth(config)
    oauth.register(
        name='oidc',
        client_id=os.environ.get("OIDC_CLIENT_ID"),
        client_secret=os.environ.get("OIDC_CLIENT_SECRET"),
        server_metadata_url=os.environ.get("OIDC_METADATA_URL"),
        client_kwargs={'scope': 'openid email profile'},
    )

    async def require_login(request: Request):
        user = request.session.get('user')
        if not user:
            redirect_uri = request.url_for('auth')
            return RedirectResponse(url=redirect_uri)
        return user

    @app.route('/login')
    async def auth(request: Request):
        redirect_uri = request.url_for('auth_callback')
        return await oauth.oidc.authorize_redirect(request, redirect_uri)

    @app.route('/auth/callback')
    async def auth_callback(request: Request):
        token = await oauth.oidc.authorize_access_token(request)
        user = await oauth.oidc.parse_id_token(request, token)
        request.session['user'] = dict(user)
        return RedirectResponse(url='/')

else:
    def require_login(request: Request):
        return None


@app.get("/proxy", include_in_schema=False)
async def proxy(url: str, headers: str = None):
    """
    Proxy endpoint to fetch the OpenAPI document from a given URL (JSON or YAML).
    """
    try:
        if headers:
            resp = requests.get(url, headers=json.loads(unquote(headers)), timeout=int(os.environ.get("PROXY_TIMEOUT", 10)))
        else:
            resp = requests.get(url, timeout=int(os.environ.get("PROXY_TIMEOUT", 10)))
        content_type = resp.headers.get("content-type", "")
        # Se for JSON, repasse como application/json
        if "json" in content_type:
            return Response(content=resp.content, media_type="application/json")
        # Se for YAML, repasse como text/yaml
        elif "yaml" in content_type or "yml" in content_type:
            return Response(content=resp.content, media_type="text/yaml")
        # Se não souber, tente detectar pelo conteúdo
        try:
            json.loads(resp.text)
            return Response(content=resp.content, media_type="application/json")
        except Exception:
            try:
                yaml.safe_load(resp.text)
                return Response(content=resp.content, media_type="text/yaml")
            except Exception:
                # Retorne como texto puro se não conseguir detectar
                return Response(content=resp.content, media_type="text/plain")
    except requests.RequestException as e:
        logger.error(f"Error fetching OpenAPI document: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to fetch OpenAPI document", "details": str(e)})

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
async def docs(request: Request, user=Depends(require_login)):
    """
    Main documentation page.
    """
    try:
        with open('static/openapi/urls.json', 'r') as f:
            swaggers = json.load(f)
            logger.info(f"Loaded {len(swaggers)} URLs.")
    except FileNotFoundError:
        logger.error("File not found: static/openapi/urls.json")
        swaggers = [
            {
                "url": "/openapi.json",
                "name": "Swagger Aggregator",
                "header": "",
            }
        ]
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from static/openapi/urls.json")
        swaggers = [
            {
                "url": "/openapi.json",
                "name": "Swagger Aggregator",
                "header": "",
            }
        ]

    for swagger in swaggers:
        swagger["url"] = apply_proxy_to_openapi(swagger.get("url"), parse_headers(swagger.get("header")))

    interface = os.environ.get("INTERFACE", "swagger-ui").lower()
    if interface not in ["swagger-ui", "redoc"]:
        interface = "swagger-ui"
    return templates.TemplateResponse(
        f"{interface}.html",
        {
            "request": request,
            "urls": swaggers,
            "title": os.environ.get("TITLE", "API Documentation"),
        }
    )

@app.get("/config", response_class=HTMLResponse, include_in_schema=False)
async def config(request: Request):
    """
    Configuration page for the OpenAPI URLs.
    """
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

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "urls": swaggers,
            "title": os.environ.get("TITLE", "API Documentation - Config"),
        }
    )