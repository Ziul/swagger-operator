# Swagger Operator

[![Build Status](https://github.com/Ziul/swagger-operator/actions/workflows/cicd.yaml/badge.svg)](https://github.com/Ziul/swagger-operator/actions)
[![Latest Release](https://img.shields.io/github/v/release/Ziul/swagger-operator?label=release&color=blue)](https://github.com/Ziul/swagger-operator/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/ziuloliveira/swagger-operator)](https://hub.docker.com/r/ziuloliveira/swagger-operator)
[![License](https://img.shields.io/github/license/Ziul/swagger-operator)](https://github.com/Ziul/swagger-operator/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

A Kubernetes operator that automatically discovers services annotated with OpenAPI/Swagger documentation and aggregates their documentation in a single UI.

## Features

- Watches Kubernetes services for specific annotations.
- Aggregates OpenAPI/Swagger endpoints from discovered services.
- Serves a dynamic Swagger UI using FastAPI.
- Easy deployment with Docker or Helm.

## Requirements

- Python 3.10+
- Kubernetes cluster
- Docker (for containerization)
- [Poetry](https://python-poetry.org/) for dependency management
- [Helm](https://helm.sh/) (optional, for easy installation)

## Getting Started

### 1. Install with Helm (recommended)

You can install the Swagger Operator easily using the Helm Chart available on Docker Hub:

```bash
helm install swagger oci://registry-1.docker.io/ziuloliveira/swagger-operator --version <DESIRED_VERSION>-chart
```

Replace `<DESIRED_VERSION>` with the desired release version.

### 2. Clone the repository (optional)

If you prefer, clone the repository for customization or local development:

```bash
git clone https://github.com/ziuloliveira/swagger-operator.git
cd swagger-operator
```

### 3. Build the Docker image

```bash
docker build -t swagger-operator:latest .
```

### 4. Deploy to Kubernetes

You can deploy the operator as a Deployment in your cluster. Make sure to set the required environment variables if you want to customize annotation keys and a service account with permissions to watch `services` events.

### 5. Annotate your services

Add the following annotation to your Kubernetes services:

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

### 6. Access the Swagger UI

Expose the operator service (default port: 80) and access `/` to see the aggregated documentation.

## Environment Variables

| Variable                        | Default                     | Description                                                                 |
|----------------------------------|-----------------------------|-----------------------------------------------------------------------------|
| `SWAGGER_OPERATOR_PATH_KEY`      | `swagger-operator-path`     | Annotation key for the OpenAPI path.                                        |
| `SWAGGER_OPERATOR_NAME_KEY`      | `swagger-operator-name`     | Annotation key for the service display name.                                |
| `SWAGGER_OPERATOR_PORT_KEY`      | `swagger-operator-port`     | Annotation key for the service port.                                        |
| `SWAGGER_OPERATOR_HEADER_KEY`    | `swagger-operator-header`   | Annotation key for extra headers.                                           |
| `PROXY_TIMEOUT`                  | `10`                        | Timeout for proxy requests (in seconds).                                    |
| `ENABLE_OIDC`                    | `false`                     | Enables (`true`) or disables (`false`) OIDC authentication.                 |
| `TITLE`                          | `API Documentation`         | Title for the Swagger UI.                                                   |
| `INTERFACE`                      | `swagger-ui`                | UI interface (`swagger-ui` or `redoc`).                                     |

## OpenID Connect (OIDC) Authentication Configuration

To enable authentication via OpenID Connect (OIDC), set the following environment variables. These allow your application to interact with an OIDC-compliant identity provider for secure authentication and authorization.

### Required Environment Variables

| Variable              | Description                                                                                 |
|-----------------------|--------------------------------------------------------------------------------------------|
| `ENABLE_OIDC`         | Enables (`true`) or disables (`false`) OIDC authentication.                                |
| `OIDC_CLIENT_ID`      | Client ID provided by the OIDC provider during registration.                               |
| `OIDC_CLIENT_SECRET`  | Client secret provided by the OIDC provider during registration.                           |
| `OIDC_METADATA_URL`   | URL to fetch the OIDC provider configuration (endpoints, public keys, etc.).               |
| `AUTH_CALLBACK`       | Callback URL where the OIDC provider will redirect after authentication.                   |

#### Example configuration

```env
ENABLE_OIDC=true
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
OIDC_METADATA_URL=https://your-oidc-provider.com/.well-known/openid-configuration
AUTH_CALLBACK=https://your-app.com/auth/callback
```

## Development

Install dependencies with Poetry:

```bash
poetry install
```

Run the FastAPI server locally:

```bash
poetry run fastapi run server.py
```

Or run the operator:

```bash
poetry run kopf run controller.py
```

## License

MIT License

---

Made with ❤️ by [Luiz Oliveira](https://github.com/ziul) and [Gustavo Coelho](https://github.com/gutorc92).