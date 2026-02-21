FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN pip install --upgrade pip && \
    pip install \
      "fastapi>=0.100" \
      "uvicorn[standard]>=0.30" \
      "pydantic>=2.0" \
      "pydantic-settings>=2.0" \
      "bcrypt>=4.0" \
      "python-multipart>=0.0.6" \
      "websockets>=16.0" \
      "sqlalchemy>=2.0" \
      "psycopg[binary]>=3.1"

