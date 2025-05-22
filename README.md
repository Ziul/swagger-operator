# Swagger Operator

[![Build Status](https://github.com/Ziul/swagger-operator/actions/workflows/cicd.yaml/badge.svg)](https://github.com/Ziul/swagger-operator/actions)
[![Latest Release](https://img.shields.io/github/v/release/Ziul/swagger-operator?label=release&color=blue)](https://github.com/Ziul/swagger-operator/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/ziuloliveira/swagger-operator)](https://hub.docker.com/r/ziuloliveira/swagger-operator)
[![License](https://img.shields.io/github/license/Ziul/swagger-operator)](https://github.com/Ziul/swagger-operator/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

A Kubernetes operator that automatically discovers services annotated with OpenAPI/Swagger documentation and aggregates their documentation in a single UI.


## Table of Contents

- [Features](#features)
- [Getting Started (Helm)](#getting-started-helm)
- [How to Annotate Your Services](#how-to-annotate-your-services)
- [Accessing the UI](#accessing-the-ui)
- [Configuration & Customization](#configuration--customization)
  - [Environment Variables](#environment-variables)
  - [OIDC Authentication (SSO)](#oidc-authentication-sso)
- [Local Development](#local-development)
- [License](#license)


## Features

- Watches Kubernetes services for specific annotations.
- Aggregates OpenAPI/Swagger endpoints from discovered services.
- Serves a dynamic Swagger UI or Redoc using FastAPI.
- Easy deployment with Helm.


## Getting Started (Helm)

Install the Swagger Operator using the Helm Chart:

```bash
helm repo add swagger-operator https://ziul.github.io/swagger-operator/
helm repo update
helm install my-release swagger-operator/swagger-operator
```


### How to Annotate Your Services

Add the following annotations to your Kubernetes services:

```yaml
metadata:
  annotations:
    swagger-operator-path: "/openapi.json"   # Path to your OpenAPI spec
    swagger-operator-name: "My Service"      # (Optional) Display name
    swagger-operator-port: "8080"            # (Optional) Service port
    swagger-operator-header: |
      Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=
      X-Custom-Header: my-value
      Another-Header: another-value
    # (Optional) Extra headers
```


### Accessing the UI

Expose the operator service (default port: 80) and access `/` to see the aggregated documentation.

---

## Configuration & Customization

### Environment Variables

You can customize the operator's behavior via environment variables:

| Variable                        | Default                     | Description                                                                 |
|----------------------------------|-----------------------------|-----------------------------------------------------------------------------|
| `SWAGGER_OPERATOR_PATH_KEY`      | `swagger-operator-path`     | Annotation key for the OpenAPI path.                                        |
| `SWAGGER_OPERATOR_NAME_KEY`      | `swagger-operator-name`     | Annotation key for the service display name.                                |
| `SWAGGER_OPERATOR_PORT_KEY`      | `swagger-operator-port`     | Annotation key for the service port.                                        |
| `SWAGGER_OPERATOR_HEADER_KEY`    | `swagger-operator-header`   | Annotation key for extra headers.                                           |
| `PROXY_TIMEOUT`                  | `10`                        | Timeout for proxy requests (in seconds).                                    |
| `ENABLE_OIDC`                    | `false`                     | Enables (`true`) or disables (`false`) OIDC authentication.                 |
| `TITLE`                          | `API Documentation`         | Title for the UI.                                                           |
| `INTERFACE`                      | `swagger-ui`                | UI interface (`swagger-ui` or `redoc`).                                     |


### OIDC Authentication (SSO)

By default, SSO is configured through the Helm chart. The following values can be set in your `values.yaml`:

```yaml
sso:
  enabled: false
  existingSecret: ""
  metadataUrl: ""
  clientSecret: ""
  clientID: ""
  authCallback: ""
```

You have two options to configure SSO:

#### 1. Using an existing Kubernetes Secret

Set `sso.existingSecret` to the name of your secret. The Secret must contain the following fields:

- `OIDC_CLIENT_SECRET`
- `ENABLE_OIDC`
- `OIDC_METADATA_URL`
- `OIDC_CLIENT_ID`
- `AUTH_CALLBACK`

**Example:**

```yaml
sso:
  enabled: true
  existingSecret: your-secret-name
```

**Example Secret:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: your-secret-name
type: Opaque
stringData:
  OIDC_CLIENT_SECRET: your-client-secret
  ENABLE_OIDC: "true"
  OIDC_METADATA_URL: https://your-oidc-provider.com/.well-known/openid-configuration
  OIDC_CLIENT_ID: your-client-id
  AUTH_CALLBACK: https://your-app.com/auth/callback
```

#### 2. Setting values directly in the Helm chart

Alternatively, you can provide the SSO configuration directly in your `values.yaml`:

```yaml
sso:
  enabled: true
  existingSecret: ""
  metadataUrl: https://your-oidc-provider.com/.well-known/openid-configuration
  clientSecret: your-client-secret
  clientID: your-client-id
  authCallback: https://your-app.com/auth/callback
```

If both `existingSecret` and the direct values are provided, the operator will prioritize the existing secret.

---

## Local Development

For local development:

1. Install dependencies with [Poetry](https://python-poetry.org/):

    ```bash
    poetry install
    ```

2. Run the FastAPI server locally:

    ```bash
    poetry run fastapi run server.py
    ```

3. Run the operator:

    ```bash
    poetry run kopf run controller.py
    ```


## License

MIT License

---

Made with ❤️ by [Luiz Oliveira](https://github.com/ziul) and [Gustavo Coelho](https://github.com/gutorc92).