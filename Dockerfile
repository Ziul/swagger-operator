FROM python:3.13-slim

# Install Poetry
RUN pip install poetry>=1.8.3
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock* README.md ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root \
    && rm -rf $POETRY_CACHE_DIR
COPY . .
RUN mkdir -p static/openapi
EXPOSE 8000

CMD ["poetry", "run", "fastapi", "run", "server.py"]
# CMD ["poetry", "run", "kopf", "run", "controller.py"]