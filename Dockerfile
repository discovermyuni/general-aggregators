FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# system deps + poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-dev

COPY . .

EXPOSE 3324

# prod server deployment using gunicorn with uvicorn worker
CMD ["gunicorn", "app:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:3324"]
