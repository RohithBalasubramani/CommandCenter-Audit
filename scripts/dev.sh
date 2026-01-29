#!/bin/bash
#
# Command Center - Unified Development Server
#
# Single-terminal dev environment with:
# - Backend (django) + Frontend (nextjs)
# - Color-coded log output
# - Persistent session logs (auto-cleanup >5 days)
# - Smart process management
#
# Usage:
#   ./scripts/dev.sh                  # Start servers (assumes setup done)
#   ./scripts/dev.sh --setup          # Run setup first, then start servers
#   ./scripts/dev.sh --full           # Full reset + setup + start
#   ./scripts/dev.sh --backend-port 8001 --frontend-port 3001
#

set -e

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  SETUP FLAGS                                                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

RUN_SETUP=false
RUN_FULL_RESET=false

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURATION - EDIT THESE FOR YOUR PROJECT                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

PROJECT_NAME="Command Center"
PROJECT_SLUG="command-center"
LOG_RETENTION_DAYS=5
BACKEND_PORT=8100
FRONTEND_PORT=3100
PERSONAPLEX_PORT=8998
BACKEND_TYPE="django"    # django | fastapi
FRONTEND_TYPE="nextjs"  # nextjs | vite

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PATHS                                                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/dev-helpers/logs"
SESSION_ID=$(date +%Y%m%d-%H%M%S)
SESSION_LOG="$LOG_DIR/session-$SESSION_ID.log"

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  COLORS                                                                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
DIM='\033[0;90m'
NC='\033[0m'
BOLD='\033[1m'

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PROCESS TRACKING                                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

BACKEND_PID=""
FRONTEND_PID=""
PERSONAPLEX_PID=""

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  LOGGING FUNCTIONS                                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

log_line() {
    local source="$1"
    local message="$2"
    local color="$3"
    local time=$(date '+%H:%M:%S')
    local full_time=$(date '+%Y-%m-%d %H:%M:%S')

    local source_color
    local source_tag
    case "$source" in
        SYSTEM)      source_tag="[SYSTEM] "; source_color="$MAGENTA" ;;
        BACKEND)     source_tag="[BACKEND]"; source_color="$YELLOW" ;;
        FRONTEND)    source_tag="[FRONTEND]"; source_color="$CYAN" ;;
        BROWSER)     source_tag="[BROWSER]"; source_color="$BLUE" ;;
        PERSONAPLEX) source_tag="[PERSONA]"; source_color="$GREEN" ;;
        *)           source_tag="         "; source_color="$WHITE" ;;
    esac

    echo -e "${DIM}[$time]${NC} ${source_color}${source_tag}${NC} ${color}${message}${NC}"
    echo "[$full_time] $source_tag $message" >> "$SESSION_LOG"
}

print_banner() {
    clear
    echo -e "${BOLD}${MAGENTA}"
    echo "    +================================================================+"
    echo "    |                                                                |"
    printf "    |      %-50s      |\n" "${PROJECT_NAME^^}"
    echo "    |      Development Server                                        |"
    echo "    |                                                                |"
    printf "    |      Session: %-43s |\n" "$SESSION_ID"
    echo "    |                                                                |"
    echo "    +================================================================+"
    echo -e "${NC}"
}

print_status() {
    local bport="$1"
    local fport="$2"
    local pport="$3"
    echo -e "${GREEN}"
    echo "    +------------------------------------------------------------------+"
    echo "    |                                                                  |"
    echo "    |    COMMAND CENTER - RUNNING                                      |"
    echo "    |                                                                  |"
    echo "    |    Layer 1 (Voice I/O):                                          |"
    printf "    |      PersonaPlex:  wss://localhost:%s/api/chat%-13s|\n" "$pport" ""
    echo "    |                                                                  |"
    echo "    |    Layer 2 (AI + RAG):                                           |"
    printf "    |      Backend API:   http://localhost:%s/api/layer2/%-9s|\n" "$bport" ""
    printf "    |      Ollama LLM:    http://localhost:11434%-22s|\n" ""
    echo "    |                                                                  |"
    echo "    |    Frontend:                                                     |"
    printf "    |      App:           http://localhost:%-26s|\n" "$fport"
    echo "    |                                                                  |"
    echo "    |    Logs:             scripts/dev-helpers/logs/                   |"
    echo "    |                                                                  |"
    echo "    |    Press Ctrl+C to stop                                          |"
    echo "    |                                                                  |"
    echo "    +------------------------------------------------------------------+"
    echo -e "${NC}"
}

print_section() {
    local title="$1"
    local line_len=$((54 - ${#title}))
    local line=$(printf '%*s' "$line_len" | tr ' ' '-')
    echo ""
    echo -e "  ${DIM}--- $title $line${NC}"
    echo ""
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CLEANUP                                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

cleanup() {
    echo ""
    log_line "SYSTEM" "Shutting down..." "$YELLOW"

    # Kill backend
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
        log_line "SYSTEM" "  Stopped backend" "$DIM"
    fi

    # Kill frontend
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
        log_line "SYSTEM" "  Stopped frontend" "$DIM"
    fi

    # Kill PersonaPlex ONLY if dev.sh started it (not the daemon)
    if [ -n "$PERSONAPLEX_PID" ] && kill -0 "$PERSONAPLEX_PID" 2>/dev/null; then
        kill "$PERSONAPLEX_PID" 2>/dev/null || true
        wait "$PERSONAPLEX_PID" 2>/dev/null || true
        log_line "SYSTEM" "  Stopped PersonaPlex" "$DIM"
    fi

    # Kill remaining processes on backend/frontend ports only
    # Do NOT kill PersonaPlex port — daemon should survive dev.sh restarts
    fuser -k $BACKEND_PORT/tcp 2>/dev/null || true
    fuser -k $FRONTEND_PORT/tcp 2>/dev/null || true

    echo ""
    log_line "SYSTEM" "Session ended: $SESSION_ID" "$DIM"
    log_line "SYSTEM" "Log saved: $SESSION_LOG" "$DIM"
    echo ""
    echo -e "    ${MAGENTA}Goodbye!${NC}"
    echo ""
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  LOG CLEANUP                                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

cleanup_old_logs() {
    if [ -d "$LOG_DIR" ]; then
        local count=$(find "$LOG_DIR" -name "session-*.log" -mtime +$LOG_RETENTION_DAYS 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            log_line "SYSTEM" "Cleaning up $count old log file(s)..." "$DIM"
            find "$LOG_DIR" -name "session-*.log" -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true
        fi
    fi
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PORT MANAGEMENT                                                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

check_port() {
    local port=$1
    if fuser $port/tcp 2>/dev/null; then
        log_line "SYSTEM" "Port $port is in use, freeing it..." "$YELLOW"
        fuser -k $port/tcp 2>/dev/null || true
        sleep 1
    fi
}

find_free_port() {
    local start_port=$1
    local port=$start_port
    while [ $port -lt $((start_port + 100)) ]; do
        if ! fuser $port/tcp 2>/dev/null; then
            echo $port
            return
        fi
        port=$((port + 1))
    done
    echo $start_port
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  OUTPUT PREFIXING                                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

prefix_output() {
    local source="$1"
    local color="$2"
    while IFS= read -r line || [ -n "$line" ]; do
        if [ -n "$line" ]; then
            local time=$(date '+%H:%M:%S')
            local full_time=$(date '+%Y-%m-%d %H:%M:%S')

            # Color based on content
            local line_color="$color"
            if echo "$line" | grep -qiE "error|exception|traceback|failed"; then
                line_color="$RED"
            elif echo "$line" | grep -qiE "warning|warn"; then
                line_color="$YELLOW"
            elif echo "$line" | grep -qE '"(GET|POST|PUT|DELETE).*" 20[0-9]'; then
                line_color="$GREEN"
            elif echo "$line" | grep -qE '"(GET|POST|PUT|DELETE).*" [45][0-9][0-9]'; then
                line_color="$RED"
            elif echo "$line" | grep -qiE "ready|compiled|started|listening"; then
                line_color="$GREEN"
            fi

            echo -e "${DIM}[$time]${NC} ${color}[$source]${NC} ${line_color}${line}${NC}"
            echo "[$full_time] [$source] $line" >> "$SESSION_LOG"
        fi
    done
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  BACKEND COMMANDS                                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

get_backend_cmd() {
    local port=$1
    case "$BACKEND_TYPE" in
        django)
            echo "python manage.py runserver 0.0.0.0:$port"
            ;;
        fastapi)
            echo "uvicorn app.main:app --reload --host 0.0.0.0 --port $port"
            ;;
        *)
            echo "uvicorn app.main:app --reload --host 0.0.0.0 --port $port"
            ;;
    esac
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  FRONTEND COMMANDS                                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

get_frontend_cmd() {
    local port=$1
    case "$FRONTEND_TYPE" in
        nextjs)
            echo "npm run dev -- -p $port"
            ;;
        vite)
            echo "npm run dev -- --port $port --host"
            ;;
        *)
            echo "npm run dev -- --port $port --host"
            ;;
    esac
}

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN                                                                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --setup)
            RUN_SETUP=true
            shift
            ;;
        --full)
            RUN_FULL_RESET=true
            RUN_SETUP=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --setup           Run setup before starting servers"
            echo "  --full            Full reset + setup + start servers"
            echo "  --backend-port N  Set backend port (default: 8100)"
            echo "  --frontend-port N Set frontend port (default: 3100)"
            echo "  --help            Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                  # Just start servers"
            echo "  $0 --setup          # Setup + start servers"
            echo "  $0 --full           # Reset everything + setup + start"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Create log directory
mkdir -p "$LOG_DIR"

# Start
print_banner

print_section "PREREQUISITES"

# Check backend venv
if [ -d "$BACKEND_DIR/venv" ]; then
    log_line "SYSTEM" "Python venv: OK" "$GREEN"
elif [ -d "$BACKEND_DIR/.venv" ]; then
    log_line "SYSTEM" "Python venv: OK" "$GREEN"
else
    log_line "SYSTEM" "Python venv not found at $BACKEND_DIR/venv" "$YELLOW"
    log_line "SYSTEM" "Will try system Python" "$DIM"
fi

# Check npm
if command -v npm &> /dev/null; then
    npm_ver=$(npm --version)
    log_line "SYSTEM" "npm: v$npm_ver" "$GREEN"
else
    log_line "SYSTEM" "npm not found!" "$RED"
    exit 1
fi

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  RUN SETUP IF REQUESTED                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if [ "$RUN_FULL_RESET" = true ]; then
    log_line "SYSTEM" "Running full reset + setup..." "$MAGENTA"
    "$SCRIPT_DIR/setup.sh" --reset
    log_line "SYSTEM" "Setup complete, starting servers..." "$GREEN"
elif [ "$RUN_SETUP" = true ]; then
    log_line "SYSTEM" "Running setup..." "$MAGENTA"
    "$SCRIPT_DIR/setup.sh"
    log_line "SYSTEM" "Setup complete, starting servers..." "$GREEN"
fi

print_section "CLEANUP"
cleanup_old_logs

# Stop existing processes on ports (but NOT PersonaPlex if daemon is running)
check_port $BACKEND_PORT
check_port $FRONTEND_PORT
# Don't kill PersonaPlex daemon — dev.sh will detect and reuse it
if [ -f /tmp/personaplex.pid ] && kill -0 "$(cat /tmp/personaplex.pid)" 2>/dev/null; then
    log_line "SYSTEM" "PersonaPlex daemon detected (PID: $(cat /tmp/personaplex.pid)) — preserving" "$GREEN"
else
    check_port $PERSONAPLEX_PORT
fi

print_section "PORTS"

actual_backend_port=$(find_free_port $BACKEND_PORT)
actual_frontend_port=$(find_free_port $FRONTEND_PORT)
actual_personaplex_port=$(find_free_port $PERSONAPLEX_PORT)

if [ "$actual_backend_port" != "$BACKEND_PORT" ]; then
    log_line "SYSTEM" "Port $BACKEND_PORT busy, using $actual_backend_port" "$YELLOW"
else
    log_line "SYSTEM" "Backend: $actual_backend_port" "$GREEN"
fi

if [ "$actual_frontend_port" != "$FRONTEND_PORT" ]; then
    log_line "SYSTEM" "Port $FRONTEND_PORT busy, using $actual_frontend_port" "$YELLOW"
else
    log_line "SYSTEM" "Frontend: $actual_frontend_port" "$GREEN"
fi

if [ "$actual_personaplex_port" != "$PERSONAPLEX_PORT" ]; then
    log_line "SYSTEM" "Port $PERSONAPLEX_PORT busy, using $actual_personaplex_port" "$YELLOW"
else
    log_line "SYSTEM" "PersonaPlex: $actual_personaplex_port" "$GREEN"
fi

print_section "OLLAMA (LLM)"

# Check if Ollama is available for RAG
if command -v ollama &> /dev/null; then
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log_line "SYSTEM" "Ollama: running" "$GREEN"
        # Show available models
        models=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | head -3 | sed 's/"name":"//g;s/"//g' | tr '\n' ', ')
        if [ -n "$models" ]; then
            log_line "SYSTEM" "  Models: $models" "$DIM"
        fi
    else
        log_line "SYSTEM" "Ollama: not running" "$YELLOW"
        log_line "SYSTEM" "  Starting Ollama in background..." "$DIM"
        ollama serve > /dev/null 2>&1 &
        sleep 2
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            log_line "SYSTEM" "  Ollama started!" "$GREEN"
        else
            log_line "SYSTEM" "  Could not start Ollama (RAG will use fallbacks)" "$YELLOW"
        fi
    fi
else
    log_line "SYSTEM" "Ollama: not installed (RAG will use fallback responses)" "$YELLOW"
    log_line "SYSTEM" "  Install: curl -fsSL https://ollama.com/install.sh | sh" "$DIM"
fi

print_section "STARTING"

# Check if PersonaPlex is already running (daemon mode)
# SSL is off by default (SSH tunnel provides encryption). Set PERSONAPLEX_SSL=true to enable.
USE_SSL="${PERSONAPLEX_SSL:-false}"
SSL_DIR="$PROJECT_DIR/personaplex/ssl"
if [ "$USE_SSL" = "true" ]; then
    PERSONAPLEX_PROTO="https"
else
    PERSONAPLEX_PROTO="http"
fi

# Check both http and https in case daemon used a different SSL setting
PERSONAPLEX_ALREADY_RUNNING=false
if curl -k -s --connect-timeout 2 "http://localhost:$actual_personaplex_port/" > /dev/null 2>&1; then
    log_line "PERSONAPLEX" "Already running on http://localhost:$actual_personaplex_port (daemon)" "$GREEN"
    PERSONAPLEX_ALREADY_RUNNING=true
    PERSONAPLEX_PID=""
elif curl -k -s --connect-timeout 2 "https://localhost:$actual_personaplex_port/" > /dev/null 2>&1; then
    log_line "PERSONAPLEX" "Already running on https://localhost:$actual_personaplex_port (daemon)" "$GREEN"
    PERSONAPLEX_ALREADY_RUNNING=true
    PERSONAPLEX_PID=""
fi

if [ "$PERSONAPLEX_ALREADY_RUNNING" = false ]; then
    # Start PersonaPlex-7B voice server (native speech-to-speech via Moshi)
    log_line "SYSTEM" "Starting PersonaPlex-7B server..." "$GREEN"
    log_line "SYSTEM" "  TIP: Run './scripts/personaplex-daemon.sh start' to keep it persistent" "$DIM"

    SSL_ARGS=""
    if [ "$USE_SSL" = "true" ]; then
        # Generate self-signed SSL certs if not present
        if [ ! -f "$SSL_DIR/cert.pem" ]; then
            log_line "SYSTEM" "  Generating SSL certs..." "$DIM"
            mkdir -p "$SSL_DIR"
            openssl req -x509 -newkey rsa:2048 -keyout "$SSL_DIR/key.pem" \
                -out "$SSL_DIR/cert.pem" -days 365 -nodes \
                -subj "/CN=localhost" 2>/dev/null
        fi
        SSL_ARGS="--ssl $SSL_DIR"
        log_line "SYSTEM" "  SSL: enabled" "$DIM"
    else
        log_line "SYSTEM" "  SSL: disabled (set PERSONAPLEX_SSL=true to enable)" "$DIM"
    fi

    (
        cd "$PROJECT_DIR/personaplex"
        if [ -d "venv" ]; then
            source venv/bin/activate
        elif [ -d ".venv" ]; then
            source .venv/bin/activate
        fi
        python3 -m moshi.server \
            --host "0.0.0.0" \
            --port "$actual_personaplex_port" \
            $SSL_ARGS \
            2>&1
    ) | prefix_output "PERSONAPLEX" "$GREEN" &
    PERSONAPLEX_PID=$!

    log_line "SYSTEM" "  PID: $PERSONAPLEX_PID" "$DIM"

    # Wait for PersonaPlex to be FULLY ready
    log_line "SYSTEM" "  Loading models (30-60 seconds)..." "$DIM"
    personaplex_ready=false
    for i in {1..90}; do
        if curl -k -s --connect-timeout 2 "${PERSONAPLEX_PROTO}://localhost:$actual_personaplex_port/" > /dev/null 2>&1; then
            personaplex_ready=true
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""

    if [ "$personaplex_ready" = true ]; then
        log_line "PERSONAPLEX" "Ready on ${PERSONAPLEX_PROTO}://localhost:$actual_personaplex_port" "$GREEN"
    else
        log_line "PERSONAPLEX" "Timeout - may still be loading" "$YELLOW"
    fi
fi

# Start backend
log_line "SYSTEM" "Starting backend ($BACKEND_TYPE)..." "$YELLOW"

backend_cmd=$(get_backend_cmd $actual_backend_port)

(
    cd "$BACKEND_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    eval "$backend_cmd" 2>&1
) | prefix_output "BACKEND" "$YELLOW" &
BACKEND_PID=$!

log_line "SYSTEM" "  PID: $BACKEND_PID" "$DIM"

# Wait for backend to be ready
log_line "SYSTEM" "Waiting for backend..." "$DIM"
ready=false
for i in {1..30}; do
    if curl -s "http://localhost:$actual_backend_port/admin/" > /dev/null 2>&1 || \
       curl -s "http://localhost:$actual_backend_port/api/" > /dev/null 2>&1 || \
       curl -s "http://localhost:$actual_backend_port/" > /dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

if [ "$ready" = true ]; then
    log_line "BACKEND" "Ready!" "$GREEN"
else
    log_line "BACKEND" "Health check timed out (may still be starting)" "$YELLOW"
fi

# Start frontend
log_line "SYSTEM" "Starting frontend ($FRONTEND_TYPE)..." "$CYAN"

frontend_cmd=$(get_frontend_cmd $actual_frontend_port)

(
    cd "$FRONTEND_DIR"
    eval "$frontend_cmd" 2>&1
) | prefix_output "FRONTEND" "$CYAN" &
FRONTEND_PID=$!

log_line "SYSTEM" "  PID: $FRONTEND_PID" "$DIM"

# Wait a bit for frontend
sleep 3

print_status $actual_backend_port $actual_frontend_port $actual_personaplex_port

print_section "LIVE LOGS"
log_line "SYSTEM" "Streaming logs... (Ctrl+C to stop)" "$DIM"

# Wait for processes
wait
