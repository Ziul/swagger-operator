FROM python:3.13-slim

# Install Poetry
RUN pip install --no-cache-dir "poetry>=1.8.3"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock* README.md ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main \
    && rm -rf $POETRY_CACHE_DIR

COPY . .

RUN mkdir -p static/openapi

# create non-root user
RUN useradd -m appuser
USER appuser

# Build-time variable for app version
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

EXPOSE 8000

CMD ["poetry", "run", "fastapi", "run", "server.py"]