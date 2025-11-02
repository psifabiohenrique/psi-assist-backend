ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION}
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y ffmpeg

RUN mkdir -p /app

WORKDIR /app


COPY pyproject.toml /app/
RUN uv sync --no-dev
COPY . /app/


RUN uv run python src/manage.py migrate
RUN uv run python src/manage.py collectstatic --noinput

EXPOSE 8000

WORKDIR /app/src

CMD ["uv", "run", "gunicorn", "--bind", ":8000", "--workers", "2", "--timeout", "600", "core.wsgi"]
# CMD ["uv", "run", "src/manage.py", "runserver"]