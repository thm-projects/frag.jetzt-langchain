FROM python:3.11.10-slim

RUN apt update && apt install -y libmagic-dev && pip install poetry==1.6.1

RUN poetry config virtualenvs.create false

WORKDIR /code

COPY ./pyproject.toml ./README.md ./poetry.lock* ./

COPY ./package[s] ./packages

RUN poetry install --no-interaction --no-ansi --no-root && pip install pyarrow==18.0.0

COPY ./app ./app

ARG SECRET_KEY
ENV SECRET_KEY=$SECRET_KEY
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV FRAGJETZT_OLLAMA_ENDPOINT="http://10.0.0.6:11434/"

RUN poetry run python -m app.cache

EXPOSE 8080

CMD exec uvicorn app.server:app --host 0.0.0.0 --port 8080 --root-path "${ROOT_PATH:-/}"
