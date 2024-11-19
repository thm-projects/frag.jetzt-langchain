FROM python:3.11-slim

RUN apt update && apt install -y libmagic-dev && pip install poetry==1.6.1

RUN poetry config virtualenvs.create false

WORKDIR /code

COPY ./pyproject.toml ./README.md ./poetry.lock* ./

COPY ./package[s] ./packages

RUN poetry install --no-interaction --no-ansi --no-root

COPY ./app ./app

RUN poetry install --no-interaction --no-ansi && pip install pyarrow==18.0.0 && poetry run python -m app.cache

EXPOSE 8080

CMD exec uvicorn app.server:app --host 0.0.0.0 --port 8080 --root-path "${ROOT_PATH:-/}"
