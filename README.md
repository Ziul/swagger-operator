# Swagger Operator

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

- `SWAGGER_OPERATOR_PATH_KEY` (default: `swagger-operator-path`)
- `SWAGGER_OPERATOR_NAME_KEY` (default: `swagger-operator-name`)
- `SWAGGER_OPERATOR_PORT_KEY` (default: `swagger-operator-port`)
- `SWAGGER_OPERATOR_HEADER_KEY` (default: `swagger-operator-header`)
- `PROXY_TIMEOUT` (default: `10`)
- `TITLE` (default: `API Documentation`)

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

Made with ❤️ by [Luiz Oliveira](https://github.com/ziul) and [Gustavo Coelho](https://github.com/gutorc92)