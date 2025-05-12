# Swagger Operator

A Kubernetes operator that automatically discovers services annotated with OpenAPI/Swagger documentation and aggregates their documentation in a single FastAPI-based UI.

## Features

- Watches Kubernetes services for specific annotations.
- Aggregates OpenAPI/Swagger endpoints from discovered services.
- Serves a dynamic Swagger UI using FastAPI.
- Easy deployment with Docker.

## Requirements

- Python 3.10+
- Kubernetes cluster
- Docker (for containerization)
- [Poetry](https://python-poetry.org/) for dependency management

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/swagger-operator.git
cd swagger-operator
```

### 2. Build the Docker image

```bash
docker build -t swagger-operator:latest .
```

### 3. Deploy to Kubernetes

You can deploy the operator as a Deployment in your cluster. Make sure to set the required environment variables if you want to customize annotation keys and a service account with permissions to watch `services` events.

### 4. Annotate your services

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

### 5. Access the Swagger UI

Expose the FastAPI server (default port: 8000) and access `/` to see the aggregated documentation.

## Environment Variables

- `SWAGGER_OPERATOR_PATH_KEY` (default: `swagger-operator-path`)
- `SWAGGER_OPERATOR_NAME_KEY` (default: `swagger-operator-name`)
- `SWAGGER_OPERATOR_PORT_KEY` (default: `swagger-operator-port`)
- `SWAGGER_OPERATOR_HEADER_KEY` (default: `swagger-operator-header`)
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

Made with ❤️ by [Luiz Oliveira](https://github.com/ziul)