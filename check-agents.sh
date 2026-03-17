#!/usr/bin/env bash
# ─── Agent Health Check Script ───────────────────────────────────────────────
# Starts the MCP server and all 4 agents locally, sends a lightweight A2A
# health/capability probe to each, prints a pass/fail summary, then cleans up.
#
# Usage:
#   ./check-agents.sh                     # run all checks
#   ./check-agents.sh --no-cleanup        # leave services running after checks
#   ./check-agents.sh --timeout 30        # custom wait timeout (seconds, default 20)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS=()
PASS=0
FAIL=0
TIMEOUT=20
CLEANUP=true

# ─── CLI flags ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-cleanup) CLEANUP=false ;;
    --timeout)    TIMEOUT="$2"; shift ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
  shift
done

# ─── Colours ───
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ─── Load .env ───
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ROOT/.env"
  set +a
fi

# ─── Helpers ───
log()  { echo -e "${CYAN}[check-agents]${RESET} $1"; }
ok()   { echo -e "  ${GREEN}✔${RESET}  $1"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}✘${RESET}  $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }

cleanup() {
  if $CLEANUP; then
    echo ""
    log "Shutting down test services..."
    for pid in "${PIDS[@]-}"; do
      kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    log "All test services stopped."
  else
    warn "Services left running (--no-cleanup). PIDs: ${PIDS[*]-}"
  fi
}
trap cleanup EXIT INT TERM

# ─── Find Python ───
find_python() {
  if [ -x "$ROOT/.venv/bin/python" ]; then echo "$ROOT/.venv/bin/python"; return; fi
  command -v python3 2>/dev/null || command -v python 2>/dev/null || true
}

PYTHON_BIN="$(find_python)"
[ -n "$PYTHON_BIN" ] || { echo "No Python interpreter found."; exit 1; }
log "Using Python: $PYTHON_BIN"

# ─── Check curl ───
command -v curl >/dev/null 2>&1 || { echo "curl is required but not found."; exit 1; }

# ─── Auth check ───
if [ -z "${GOOGLE_API_KEY:-}" ] && [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${GOOGLE_CLOUD_PROJECT:-}" ]; then
  warn "No model credentials detected (GOOGLE_API_KEY / GEMINI_API_KEY / GOOGLE_CLOUD_PROJECT)."
  warn "Agents will start but LLM calls will fail at inference time."
else
  if [ -n "${GOOGLE_CLOUD_PROJECT:-}" ]; then
    export GOOGLE_GENAI_USE_VERTEXAI="${GOOGLE_GENAI_USE_VERTEXAI:-1}"
    export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
    log "Auth: Vertex AI (project: $GOOGLE_CLOUD_PROJECT)"
  else
    log "Auth: Gemini API key"
  fi
fi

# ─── Port helpers ───
port_is_free() {
  ! (: < /dev/tcp/localhost/"$1") 2>/dev/null
}

wait_for_port() {
  local port="$1"
  local label="$2"
  local deadline=$((SECONDS + TIMEOUT))
  while [ $SECONDS -lt $deadline ]; do
    if (: < /dev/tcp/localhost/"$port") 2>/dev/null; then
      return 0
    fi
    sleep 1
  done
  return 1
}

next_free_port() {
  local p="$1"
  while ! port_is_free "$p"; do p=$((p + 1)); done
  echo "$p"
}

# ─── Resolve ports ───
MCP_PORT="$(next_free_port "${MCP_PORT:-8080}")"
PORT_CREATEWORLD="$(next_free_port "${AGENT_CREATEWORLD_PORT:-10001}")"
PORT_CREATECHARACTER="$(next_free_port "${AGENT_CREATECHARACTER_PORT:-10002}")"
PORT_NARRATIVE="$(next_free_port "${AGENT_NARRATIVE_PORT:-10003}")"
PORT_OPTIONGEN="$(next_free_port "${AGENT_OPTIONGEN_PORT:-10004}")"

log "Ports → MCP:$MCP_PORT  createworld:$PORT_CREATEWORLD  createcharacter:$PORT_CREATECHARACTER  narrative:$PORT_NARRATIVE  optiongen:$PORT_OPTIONGEN"

# ─── Start a background service ───
start_bg() {
  local name="$1"
  local workdir="$2"
  shift 2
  log "Starting $name..."
  (cd "$workdir" && "$@") >> "/tmp/check-agents-${name// /-}.log" 2>&1 &
  PIDS+=("$!")
}

# ─── 1. MCP Server ───
start_bg "mcp-server" "$ROOT/mcp-server" \
  env PORT="$MCP_PORT" "$PYTHON_BIN" server.py

# ─── 2. Agents ───
UVICORN=("$PYTHON_BIN" -m uvicorn)

start_bg "agent-createworld" "$ROOT/agent-createworld" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$PORT_CREATEWORLD" \
  "${UVICORN[@]}" agent:a2a_app --host 0.0.0.0 --port "$PORT_CREATEWORLD"

start_bg "agent-createcharacter" "$ROOT/agent-createcharacter" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$PORT_CREATECHARACTER" \
  "${UVICORN[@]}" agent:a2a_app --host 0.0.0.0 --port "$PORT_CREATECHARACTER"

start_bg "agent-narrative" "$ROOT/agent-narrative" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$PORT_NARRATIVE" \
  "${UVICORN[@]}" agent:a2a_app --host 0.0.0.0 --port "$PORT_NARRATIVE"

start_bg "agent-optiongeneration" "$ROOT/agent-optiongeneration" \
  env MCP_SERVER_URL="http://localhost:$MCP_PORT" PORT="$PORT_OPTIONGEN" \
  "${UVICORN[@]}" agent:a2a_app --host 0.0.0.0 --port "$PORT_OPTIONGEN"

# ─── Wait & probe each service ───
echo ""
echo -e "${BOLD}━━━  Waiting for services to become ready  ━━━${RESET}"

check_service() {
  local label="$1"
  local port="$2"
  local path="${3:-.well-known/agent.json}"   # A2A agent card endpoint

  log "Probing $label on :$port ..."

  if ! wait_for_port "$port" "$label"; then
    fail "$label — did NOT start within ${TIMEOUT}s (port $port never opened)"
    warn "Log: /tmp/check-agents-${label// /-}.log"
    return
  fi

  # HTTP probe
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 10 \
    "http://localhost:${port}/${path}" 2>/dev/null || echo "000")

  if [[ "$http_code" == "200" ]]; then
    ok "$label — HTTP $http_code ✓  (http://localhost:${port}/${path})"
  elif [[ "$http_code" == "000" ]]; then
    fail "$label — no response / connection refused"
  else
    # Any non-200 that isn't a connection failure means the server is running
    # (e.g. 404 if path differs, 422 for missing body, etc.)
    warn "$label — server responded HTTP $http_code (port open, but check the path)"
    ok "$label — server is UP (http://localhost:${port})"
  fi
}

# Allow a small grace period for processes to bind
sleep 2

check_service "mcp-server"            "$MCP_PORT"            "health"
check_service "agent-createworld"     "$PORT_CREATEWORLD"    ".well-known/agent.json"
check_service "agent-createcharacter" "$PORT_CREATECHARACTER" ".well-known/agent.json"
check_service "agent-narrative"       "$PORT_NARRATIVE"      ".well-known/agent.json"
check_service "agent-optiongeneration" "$PORT_OPTIONGEN"     ".well-known/agent.json"

# ─── Summary ───
echo ""
echo -e "${BOLD}━━━  Summary  ━━━${RESET}"
echo -e "  ${GREEN}Passed: $PASS${RESET}   ${RED}Failed: $FAIL${RESET}"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo -e "${YELLOW}Logs are in /tmp/check-agents-*.log${RESET}"
  echo ""
  echo -e "${YELLOW}Tip:${RESET} If an agent failed to start, check:"
  echo "  1. Python deps installed?  →  $PYTHON_BIN -m pip install -r <agent>/requirements.txt"
  echo "  2. Credentials set?        →  GOOGLE_API_KEY / GEMINI_API_KEY / GOOGLE_CLOUD_PROJECT"
  echo "  3. MCP server started OK?  →  cat /tmp/check-agents-mcp-server.log"
  echo ""
  exit 1
fi

echo -e "${GREEN}All agents are healthy!${RESET}"
