from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import requests
import logging
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import secrets

logger = logging.getLogger("uvicorn.error")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32), max_age=None)


# static files
app.mount("/openapi", StaticFiles(directory="static/openapi"), name="openapi")
# templates
templates = Jinja2Templates(directory="templates")

ENABLE_OIDC = os.environ.get("ENABLE_OIDC", "false").lower() == "true"
AUTH_CALLBACK = os.environ.get("AUTH_CALLBACK", None)
config = Config()  # ou use variáveis de ambiente diretamente
oauth = OAuth(config)


if ENABLE_OIDC:
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
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/login"}
            )
        return user

    @app.route('/login')
    async def auth(request: Request):
        redirect_uri = AUTH_CALLBACK or request.url_for('auth_callback')
        return await oauth.oidc.authorize_redirect(request, redirect_uri)

    @app.route('/auth/callback')
    async def auth_callback(request: Request):
        token = await oauth.oidc.authorize_access_token(request)
        request.session['user'] = dict(token['userinfo'])
        return RedirectResponse(url='/')

else:
    def require_login(request: Request):
        request.session['user'] = "anonymous"
        return request.session['user']

@app.get("/services/{name}", response_class=HTMLResponse, include_in_schema=False)
async def services(request: Request, name: str, user=Depends(require_login)):
    with open('static/openapi/services.json', 'r') as f:
        services = json.load(f)
        logger.info(f"Loaded {len(services)} services.")
    if name not in services:
        logger.error(f"Service {name} not found.")
        raise HTTPException(status_code=404, detail="Service not found")
    service = services[name]
    if not service:
        logger.error(f"Service {name} not found.")
        raise HTTPException(status_code=404, detail="Service not found")
    resp = requests.get(service['url'], timeout=int(os.environ.get("PROXY_TIMEOUT", 10)), headers=parse_headers(service.get("header")))
    content_type = resp.headers.get("content-type", "")
    # Se for JSON, repasse como application/json
    if "json" in content_type:
        return Response(content=resp.content, media_type="application/json")
    # Se for YAML, repasse como text/yaml
    elif "yaml" in content_type or "yml" in content_type:
        return Response(content=resp.content, media_type="text/yaml")
    else:
        logger.error(f"Unsupported content type: {content_type}")
        raise HTTPException(status_code=400, detail="Unsupported content type")

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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, template:str='swagger-ui', user=Depends(require_login)):
    if template.lower() not in ["redoc", "swagger-ui"]:
        raise HTTPException(status_code=400, detail="Invalid template. Use 'redoc' or 'swagger-ui'.")

    try:
        with open('static/openapi/services.json', 'r') as f:
            services = json.load(f)
            logger.info(f"Loaded {len(services)} services.")
    except Exception as e:
        logger.error(f"Error loading services file: {e}")
        raise HTTPException(status_code=500, detail="Error loading services file.")
    
    urls = []
    for service_name, service in services.items():
        urls.append({
            "url": f"/services/{service_name}",
            "name": service['name'],
            "header": service.get("header", ""),
        })

    match template.lower():
        case "redoc":
            return templates.TemplateResponse(
                "redoc.html",
                {
                    "request": request,
                    "urls": urls,
                    "title": os.environ.get("TITLE", "API Documentation"),
                }
            )
        case "swagger-ui":
            return templates.TemplateResponse(
                "swagger-ui.html",
                {
                    "request": request,
                    "urls": urls,
                    "title": os.environ.get("TITLE", "API Documentation"),
                }
            )
        case _:
            logger.error(f"Invalid template: {template}")
            raise HTTPException(status_code=400, detail="Invalid template. Use 'redoc' or 'swagger-ui'.")


@app.get("/config", response_class=HTMLResponse, include_in_schema=False)
async def config(request: Request, user=Depends(require_login)):
    """
    Configuration page for the OpenAPI URLs.
    """
    try:
        with open('static/openapi/urls.json') as f:
            swaggers = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration file: {e}")
        swaggers = []
        request.session['error'] = "Error loading configuration file."

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "urls": swaggers,
            "title": os.environ.get("TITLE", "Swagger Operator"),
            "version": os.environ.get("SWAGGER_OPERATOR_VERSION", ""),
            "compiling_version": os.environ.get("APP_VERSION", ""),
            "session": request.session,
            "settings": {
                "enable_oidc": ENABLE_OIDC,
                "oidc_client_id": os.environ.get("OIDC_CLIENT_ID"),
                "oidc_metadata_url": os.environ.get("OIDC_METADATA_URL"),
                "interface": os.environ.get("INTERFACE", "swagger-ui").lower(),
                "path_key": os.environ.get("SWAGGER_OPERATOR_PATH_KEY", "swagger-operator-path"),
                "name_key": os.environ.get("SWAGGER_OPERATOR_NAME_KEY", "swagger-operator-name"),
                "port_key": os.environ.get("SWAGGER_OPERATOR_PORT_KEY", "swagger-operator-port"),
                "header_key": os.environ.get("SWAGGER_OPERATOR_HEADER_KEY", "swagger-operator-header"),
                "proxy_timeout": os.environ.get("PROXY_TIMEOUT", 10),
            }
        }
    )