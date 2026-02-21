#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.backend-dev.yml"
PYTHON_BIN="${PYTHON_BIN:-python3}"

ACTION="${1:-up}"
if [[ $# -gt 0 ]]; then
  shift
fi

PRINT_ONLY="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --print-only)
      PRINT_ONLY="true"
      shift
      ;;
    *)
      EXTRA_ARG="$1" "${PYTHON_BIN}" - <<'PY'
import json
import os
import sys

payload = {
    "success": False,
    "error": {
        "code": "INVALID_ARGUMENT",
        "message": f"unknown option: {os.environ.get('EXTRA_ARG', '')}",
    },
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
sys.exit(1)
PY
      ;;
  esac
done

export POSTGRES_USER="${POSTGRES_USER:-quantpoly}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-quantpoly}"
export POSTGRES_DB="${POSTGRES_DB:-quantpoly_test}"
export POSTGRES_PORT="${POSTGRES_PORT:-54329}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export PROJECT_NAME="${PROJECT_NAME:-quantpoly-backend-dev}"
export BACKEND_STORAGE_BACKEND="${BACKEND_STORAGE_BACKEND:-postgres}"
export BACKEND_POSTGRES_DSN="${BACKEND_POSTGRES_DSN:-postgresql+psycopg://quantpoly:quantpoly@postgres:5432/${POSTGRES_DB}}"
export BACKEND_CORS_ALLOWED_ORIGINS="${BACKEND_CORS_ALLOWED_ORIGINS:-http://localhost:3300}"
export BACKEND_CORS_ALLOW_CREDENTIALS="${BACKEND_CORS_ALLOW_CREDENTIALS:-true}"
export BACKEND_CORS_ALLOW_METHODS="${BACKEND_CORS_ALLOW_METHODS:-GET,POST,PUT,PATCH,DELETE,OPTIONS}"
export BACKEND_CORS_ALLOW_HEADERS="${BACKEND_CORS_ALLOW_HEADERS:-*}"
export BACKEND_LOG_LEVEL="${BACKEND_LOG_LEVEL:-warning}"

UP_CMD="docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} up -d --build postgres backend_dev"
DOWN_CMD="docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} down"
STATUS_CMD="docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} ps"
LOGS_CMD="docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} logs -f backend_dev"
export COMPOSE_FILE
export UP_CMD
export DOWN_CMD
export STATUS_CMD
export LOGS_CMD

print_plan_json() {
  local action_json="$1"
  ACTION_JSON="${action_json}" "${PYTHON_BIN}" - <<'PY'
import json
import os

payload = {
    "success": True,
    "action": os.environ["ACTION_JSON"],
    "compose_file": os.environ["COMPOSE_FILE"],
    "env": {
        "POSTGRES_USER": os.environ["POSTGRES_USER"],
        "POSTGRES_DB": os.environ["POSTGRES_DB"],
        "POSTGRES_PORT": os.environ["POSTGRES_PORT"],
        "BACKEND_PORT": os.environ["BACKEND_PORT"],
        "PROJECT_NAME": os.environ["PROJECT_NAME"],
        "BACKEND_STORAGE_BACKEND": os.environ["BACKEND_STORAGE_BACKEND"],
        "BACKEND_POSTGRES_DSN": os.environ["BACKEND_POSTGRES_DSN"],
        "BACKEND_CORS_ALLOWED_ORIGINS": os.environ["BACKEND_CORS_ALLOWED_ORIGINS"],
        "BACKEND_CORS_ALLOW_CREDENTIALS": os.environ["BACKEND_CORS_ALLOW_CREDENTIALS"],
        "BACKEND_CORS_ALLOW_METHODS": os.environ["BACKEND_CORS_ALLOW_METHODS"],
        "BACKEND_CORS_ALLOW_HEADERS": os.environ["BACKEND_CORS_ALLOW_HEADERS"],
    },
    "commands": {
        "up": os.environ["UP_CMD"],
        "down": os.environ["DOWN_CMD"],
        "status": os.environ["STATUS_CMD"],
        "logs": os.environ["LOGS_CMD"],
    },
    "origins": {
        "frontend": os.environ["BACKEND_CORS_ALLOWED_ORIGINS"],
        "backend": f"http://localhost:{os.environ['BACKEND_PORT']}",
    },
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY
}

print_error_json() {
  local code="$1"
  local message="$2"
  ERROR_CODE="$code" ERROR_MESSAGE="$message" "${PYTHON_BIN}" - <<'PY'
import json
import os

payload = {
    "success": False,
    "error": {
        "code": os.environ["ERROR_CODE"],
        "message": os.environ["ERROR_MESSAGE"],
    },
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    print_error_json "DEPENDENCY_MISSING" "docker command not found"
    exit 1
  fi
}

wait_backend_health() {
  local url="http://localhost:${BACKEND_PORT}/health"
  local max_attempts=60
  local attempt=1
  while [[ ${attempt} -le ${max_attempts} ]]; do
    if curl -fsS "${url}" >/tmp/quantpoly_backend_health.json 2>/dev/null; then
      if grep -q '"success":true' /tmp/quantpoly_backend_health.json; then
        return 0
      fi
    fi
    sleep 2
    attempt=$((attempt + 1))
  done
  return 1
}

case "${ACTION}" in
  up|down|status|logs)
    ;;
  *)
    print_error_json "INVALID_ARGUMENT" "unknown action: ${ACTION}"
    exit 1
    ;;
esac

if [[ "${PRINT_ONLY}" == "true" ]]; then
  print_plan_json "${ACTION}"
  exit 0
fi

require_docker

case "${ACTION}" in
  up)
    bash -c "${UP_CMD}"
    if ! wait_backend_health; then
      print_error_json "STARTUP_FAILED" "backend health check timeout: http://localhost:${BACKEND_PORT}/health"
      exit 1
    fi
    print_plan_json "up"
    ;;
  down)
    bash -c "${DOWN_CMD}"
    print_plan_json "down"
    ;;
  status)
    bash -c "${STATUS_CMD}"
    print_plan_json "status"
    ;;
  logs)
    bash -c "${LOGS_CMD}"
    ;;
esac
