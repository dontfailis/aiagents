#!/usr/bin/env bash
set -euo pipefail

# ─── Shared AI Storytelling RPG — Local Dev Runner ───
# Starts all services: MCP server, 4 agents, frontend gateway, and React frontend.
# Usage: ./run-local.sh
# Stop:  Ctrl-C (kills all background processes)

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS=()

if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ROOT/.env"
  set +a
fi

log() {
  echo "[run-local] $1"
}

fail() {
  log "$1"
  exit 1
}

cleanup() {
  echo ""
  echo "Shutting down all services..."
  for pid in "${PIDS[@]-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null
  echo "All services stopped."
}
trap cleanup EXIT INT TERM

find_python() {
  if [ -x "$ROOT/.venv/bin/python" ]; then
    echo "$ROOT/.venv/bin/python"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    echo "$(command -v python3)"
    return
  fi

  if command -v python >/dev/null 2>&1; then
    echo "$(command -v python)"
    return
  fi

  return 1
}

ensure_python_deps() {
  if "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import importlib.util
import sys

required = ("uvicorn", "fastapi", "httpx", "a2a.client", "a2a.server.apps", "fastmcp")
missing = [name for name in required if importlib.util.find_spec(name) is None]
sys.exit(1 if missing else 0)
PY
  then
    return
  fi

  fail "Python dependencies are missing or incompatible for $PYTHON_BIN. Install them with: $PYTHON_BIN -m pip install -r requirements.txt"
}

configure_model_auth() {
  if [ -n "${GOOGLE_API_KEY:-}" ] || [ -n "${GEMINI_API_KEY:-}" ]; then
    log "Using Gemini API key auth for ADK agents."
    return
  fi

  if [ -n "${GOOGLE_CLOUD_PROJECT:-}" ]; then
    export GOOGLE_GENAI_USE_VERTEXAI="${GOOGLE_GENAI_USE_VERTEXAI:-1}"
    export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
    log "No API key found; using Vertex AI auth for project $GOOGLE_CLOUD_PROJECT."
    return
  fi

  fail "No model credentials configured. Set GOOGLE_API_KEY or GEMINI_API_KEY, or provide GOOGLE_CLOUD_PROJECT with ADC/Vertex auth."
}

port_is_free() {
  local port="$1"

  if "$PYTHON_BIN" -c "import socket, sys; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); ok=True
try:
    s.bind(('0.0.0.0', int(sys.argv[1])))
except OSError:
    ok=False
finally:
    s.close()
raise SystemExit(0 if ok else 1)" "$port"; then
    return 0
  fi

  return 1
}

resolve_port() {
  local requested_port="$1"
  local label="$2"
  local max_tries="${3:-200}"
  local candidate="$requested_port"
  local attempt=0

  while [ "$attempt" -lt "$max_tries" ]; do
    if port_is_free "$candidate"; then
      if [ "$candidate" != "$requested_port" ]; then
        echo "[run-local] $label port $requested_port is busy, using :$candidate instead." >&2
      fi
      echo "$candidate"
      return 0
    fi
    candidate=$((candidate + 1))
    attempt=$((attempt + 1))
  done

  fail "Could not find a free port for $label starting from $requested_port."
}

start_service() {
  local name="$1"
  local workdir="$2"
  shift 2

  log "Starting $name..."
  (
    cd "$workdir"
    "$@"
  ) &
  local pid=$!
  PIDS+=("$pid")

  sleep 1
  if ! kill -0 "$pid" 2>/dev/null; then
    fail "$name failed to start. Check the error output above."
  fi
}

PYTHON_BIN="$(find_python || true)"
[ -n "$PYTHON_BIN" ] || fail "No Python interpreter found. Install python3 or create $ROOT/.venv first."
UVICORN_CMD=("$PYTHON_BIN" -m uvicorn)
MCP_PORT="${MCP_PORT:-8080}"
AGENT_CREATEWORLD_PORT="${AGENT_CREATEWORLD_PORT:-10001}"
AGENT_CREATECHARACTER_PORT="${AGENT_CREATECHARACTER_PORT:-10002}"
AGENT_NARRATIVE_PORT="${AGENT_NARRATIVE_PORT:-10003}"
AGENT_OPTIONGEN_PORT="${AGENT_OPTIONGEN_PORT:-10004}"
GATEWAY_PORT="${GATEWAY_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

ensure_python_deps
configure_model_auth

command -v npm >/dev/null 2>&1 || fail "npm is required but was not found on PATH."

MCP_PORT="$(resolve_port "$MCP_PORT" "MCP server")"
AGENT_CREATEWORLD_PORT="$(resolve_port "$AGENT_CREATEWORLD_PORT" "agent-createworld")"
AGENT_CREATECHARACTER_PORT="$(resolve_port "$AGENT_CREATECHARACTER_PORT" "agent-createcharacter")"
AGENT_NARRATIVE_PORT="$(resolve_port "$AGENT_NARRATIVE_PORT" "agent-narrative")"
AGENT_OPTIONGEN_PORT="$(resolve_port "$AGENT_OPTIONGEN_PORT" "agent-optiongeneration")"
GATEWAY_PORT="$(resolve_port "$GATEWAY_PORT" "frontend-web gateway")"
FRONTEND_PORT="$(resolve_port "$FRONTEND_PORT" "React frontend")"

# ─── Install frontend deps if needed ───
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  log "Installing frontend dependencies..."
  (cd "$ROOT/frontend" && npm install)
fi

# ─── 1. MCP Server (database layer) — port 8080 ───
start_service \
  "MCP Server on :$MCP_PORT" \
  "$ROOT/mcp-server" \
  env PORT="$MCP_PORT" "$PYTHON_BIN" server.py

# ─── 2. Agents — ports 10001-10004 ───
start_service \
  "agent-createworld on :$AGENT_CREATEWORLD_PORT" \
  "$ROOT/agent-createworld" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$AGENT_CREATEWORLD_PORT" "${UVICORN_CMD[@]}" agent:a2a_app --host 0.0.0.0 --port "$AGENT_CREATEWORLD_PORT"

start_service \
  "agent-createcharacter on :$AGENT_CREATECHARACTER_PORT" \
  "$ROOT/agent-createcharacter" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$AGENT_CREATECHARACTER_PORT" "${UVICORN_CMD[@]}" agent:a2a_app --host 0.0.0.0 --port "$AGENT_CREATECHARACTER_PORT"

start_service \
  "agent-narrative on :$AGENT_NARRATIVE_PORT" \
  "$ROOT/agent-narrative" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$AGENT_NARRATIVE_PORT" "${UVICORN_CMD[@]}" agent:a2a_app --host 0.0.0.0 --port "$AGENT_NARRATIVE_PORT"

start_service \
  "agent-optiongeneration on :$AGENT_OPTIONGEN_PORT" \
  "$ROOT/agent-optiongeneration" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$AGENT_OPTIONGEN_PORT" "${UVICORN_CMD[@]}" agent:a2a_app --host 0.0.0.0 --port "$AGENT_OPTIONGEN_PORT"

# ─── 3. Frontend Gateway — port 8000 ───
start_service \
  "frontend-web gateway on :$GATEWAY_PORT" \
  "$ROOT/frontend-web" \
  env \
    PUBLIC_API_BASE_URL="http://localhost:$GATEWAY_PORT" \
    FRONTEND_ORIGIN="http://localhost:$FRONTEND_PORT" \
    FRONTEND_ORIGIN_ALT="http://127.0.0.1:$FRONTEND_PORT" \
    AGENT_CREATEWORLD_URL="http://localhost:$AGENT_CREATEWORLD_PORT" \
    AGENT_CREATECHARACTER_URL="http://localhost:$AGENT_CREATECHARACTER_PORT" \
    AGENT_NARRATIVE_URL="http://localhost:$AGENT_NARRATIVE_PORT" \
    AGENT_OPTIONGEN_URL="http://localhost:$AGENT_OPTIONGEN_PORT" \
    "${UVICORN_CMD[@]}" main:app --host 0.0.0.0 --port "$GATEWAY_PORT"

# ─── 4. React Frontend — port 5173 ───
start_service \
  "React frontend on :$FRONTEND_PORT" \
  "$ROOT/frontend" \
  env VITE_API_BASE_URL="http://localhost:$GATEWAY_PORT" npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"

echo ""
echo "════════════════════════════════════════════"
echo "  All services running!"
echo ""
echo "  Frontend:   http://localhost:$FRONTEND_PORT"
echo "  Gateway:    http://localhost:$GATEWAY_PORT"
echo "  MCP Server: http://localhost:$MCP_PORT"
echo "  Agents:     :$AGENT_CREATEWORLD_PORT :$AGENT_CREATECHARACTER_PORT :$AGENT_NARRATIVE_PORT :$AGENT_OPTIONGEN_PORT"
echo ""
echo "  Press Ctrl-C to stop everything."
echo "════════════════════════════════════════════"
echo ""

wait
