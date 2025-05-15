from fastapi import FastAPI, Request, HTTPException
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
# templates
templates = Jinja2Templates(directory="templates")


@app.get("/proxy", include_in_schema=False)
async def proxy(url: str, headers: str = None):
    """
    Proxy endpoint to fetch the OpenAPI JSON from a given URL.
    """
    try:
        if headers:
            response = requests.get(url, headers=json.loads(unquote(headers)), timeout=int(os.environ.get("PROXY_TIMEOUT", 10)))
        else:
            response = requests.get(url, timeout=int(os.environ.get("PROXY_TIMEOUT", 10)))
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching OpenAPI JSON: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to fetch OpenAPI JSON", "details": str(e)})

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

    return templates.TemplateResponse(
        "swagger.html",
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