FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /code

COPY ./pyproject.toml ./README.md ./
COPY ./app ./app

RUN uv pip install --system --default-index https://pypi.org/simple -e .

ARG AGENT_VERSION=0.0.0
ENV AGENT_VERSION=${AGENT_VERSION}

EXPOSE 8080

CMD ["uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
