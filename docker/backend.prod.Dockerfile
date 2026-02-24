FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BACKEND_STORAGE_BACKEND=postgres \
    BACKEND_LOG_LEVEL=warning

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

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

COPY apps ./apps
COPY libs ./libs
COPY scripts ./scripts

ENV PYTHONPATH="/workspace:/workspace/libs/platform_core:/workspace/libs/user_auth:/workspace/libs/monitoring_realtime:/workspace/libs/strategy_management:/workspace/libs/backtest_runner:/workspace/libs/trading_account:/workspace/libs/market_data:/workspace/libs/risk_control:/workspace/libs/signal_execution:/workspace/libs/data_topology_boundary:/workspace/libs/job_orchestration:/workspace/libs/admin_governance:/workspace/libs/user_preferences"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=20s \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "apps.backend_app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
