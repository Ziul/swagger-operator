import kopf
import os
from urllib.parse import urlunparse


@kopf.on.startup()
def configure(memo: kopf.Memo, **_):
    memo.apps = {}

@kopf.on.cleanup()
async def cleanup_fn(logger, **kwargs):
    logger.info("Cleaning up resources...")

@kopf.on.event('v1', 'services', 
                annotations={os.environ.get('SWAGGER_OPERATOR_PATH_KEY', 'swagger-operator-path'):kopf.PRESENT},
               )
def create_fn(event, memo: kopf.Memo, logger, **kwargs):
    """
    This function is called when a new resource is created.
    It prints the event type and the resource name.
    """
    path_key = os.environ.get('SWAGGER_OPERATOR_PATH_KEY', 'swagger-operator-path')
    name_key = os.environ.get('SWAGGER_OPERATOR_NAME_KEY', 'swagger-operator-name')
    name_port = os.environ.get('SWAGGER_OPERATOR_PORT_KEY', 'swagger-operator-port')
    annotations = event['object']['metadata'].get('annotations', {})

    application_path = annotations[path_key]
    application_port = annotations.get(name_port, '80')
    service_name = event['object']['metadata']['name']
    application_name = annotations.get(name_key, service_name)
    namespace = event['object']['metadata']['namespace']

    if not application_path.startswith('/'):
        application_path = "/" + application_path

    netloc = f"{service_name}.{namespace}.svc.cluster.local:{application_port}"

    if event['type'] == 'DELETED':
        if f"{namespace}/{application_name}" in memo.apps:
            del memo.apps[f"{namespace}/{application_name}"]
    else:
        memo.apps.update({f"{namespace}/{application_name}": {
            'url': urlunparse(("http", netloc, application_path, '', '', '')),
            'name': application_name,
        }})

    logger.debug(list(memo.apps.keys()))
    logger.debug(list(memo.apps.values()))
    urls = list(memo.apps.values())
    with open('static/openapi/urls.json', 'w') as file:
        file.write(str(urls).replace("'", '"'))
        logger.info("URLs written to file.")