import kopf
import os
from urllib.parse import urlunparse, urlparse



@kopf.on.startup()
def configure(memo: kopf.Memo, **_):
    memo.apps = {}

@kopf.on.cleanup()
async def cleanup_fn(logger, **kwargs):
    logger.info("Cleaning up resources...")

@kopf.on.event('v1', 'services', 
                annotations={os.environ.get('SWAGGER_OPERATOR_PATH_KEY', 'swagger-operator-path'):kopf.PRESENT},
               )
def service_event(event, memo: kopf.Memo, logger, **kwargs):
    path_key = os.environ.get('SWAGGER_OPERATOR_PATH_KEY', 'swagger-operator-path')
    name_key = os.environ.get('SWAGGER_OPERATOR_NAME_KEY', 'swagger-operator-name')
    name_port = os.environ.get('SWAGGER_OPERATOR_PORT_KEY', 'swagger-operator-port')
    annotations = event['object']['metadata'].get('annotations', {})

    application_path = annotations[path_key]
    application_port = annotations.get(name_port, '80')
    service_name = event['object']['metadata']['name']
    application_name = annotations.get(name_key, service_name)
    namespace = event['object']['metadata']['namespace']

    application_url = urlparse(application_path)
    if not application_url.netloc:
        if not application_url.path.startswith('/'):
            application_url = urlparse(f"/{application_url.path}")
        application_url = urlparse(f"http://{service_name}.{namespace}.svc.cluster.local:{application_port}{application_path}")



    if event['type'] == 'DELETED':
        if f"{namespace}/{application_name}" in memo.apps:
            del memo.apps[f"{namespace}/{application_name}"]
    else:
        memo.apps.update({f"{namespace}/{application_name}": {
            'url': urlunparse(application_url),
            'name': application_name,
        }})

    logger.debug(list(memo.apps.keys()))
    logger.debug(list(memo.apps.values()))
    urls = list(memo.apps.values())
    with open('static/openapi/urls.json', 'w') as file:
        file.write(str(urls).replace("'", '"'))
        logger.info("URLs written to file.")