#!/usr/bin/env bash
set -e

# ─── Shared AI Storytelling RPG — Local Dev Runner ───
# Starts all services: MCP server, 4 agents, frontend gateway, and React frontend.
# Usage: ./run-local.sh
# Stop:  Ctrl-C (kills all background processes)

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS=()

cleanup() {
  echo ""
  echo "Shutting down all services..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null
  echo "All services stopped."
}
trap cleanup EXIT INT TERM

log() {
  echo "[run-local] $1"
}

# ─── Install frontend deps if needed ───
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  log "Installing frontend dependencies..."
  (cd "$ROOT/frontend" && npm install)
fi

# ─── 1. MCP Server (database layer) — port 8080 ───
log "Starting MCP Server on :8080..."
(cd "$ROOT/mcp-server" && PORT=8080 python server.py) &
PIDS+=($!)

sleep 2

# ─── 2. Agents — ports 10001-10004 ───
log "Starting agent-createworld on :10001..."
(cd "$ROOT/agent-createworld" && MCP_SERVER_URL=http://localhost:8080 PORT=10001 uvicorn agent:a2a_app --port 10001) &
PIDS+=($!)

log "Starting agent-createcharacter on :10002..."
(cd "$ROOT/agent-createcharacter" && MCP_SERVER_URL=http://localhost:8080 PORT=10002 uvicorn agent:a2a_app --port 10002) &
PIDS+=($!)

log "Starting agent-narrative on :10003..."
(cd "$ROOT/agent-narrative" && MCP_SERVER_URL=http://localhost:8080 PORT=10003 uvicorn agent:a2a_app --port 10003) &
PIDS+=($!)

log "Starting agent-optiongeneration on :10004..."
(cd "$ROOT/agent-optiongeneration" && MCP_SERVER_URL=http://localhost:8080 PORT=10004 uvicorn agent:a2a_app --port 10004) &
PIDS+=($!)

sleep 2

# ─── 3. Frontend Gateway — port 8000 ───
log "Starting frontend-web gateway on :8000..."
(cd "$ROOT/frontend-web" && \
  AGENT_CREATEWORLD_URL=http://localhost:10001 \
  AGENT_CREATECHARACTER_URL=http://localhost:10002 \
  AGENT_NARRATIVE_URL=http://localhost:10003 \
  AGENT_OPTIONGEN_URL=http://localhost:10004 \
  uvicorn main:app --port 8000) &
PIDS+=($!)

# ─── 4. React Frontend — port 5173 ───
log "Starting React frontend on :5173..."
(cd "$ROOT/frontend" && npm run dev) &
PIDS+=($!)

echo ""
echo "════════════════════════════════════════════"
echo "  All services running!"
echo ""
echo "  Frontend:   http://localhost:5173"
echo "  Gateway:    http://localhost:8000"
echo "  MCP Server: http://localhost:8080"
echo "  Agents:     :10001 :10002 :10003 :10004"
echo ""
echo "  Press Ctrl-C to stop everything."
echo "════════════════════════════════════════════"
echo ""

wait