#!/usr/bin/env bash
# Vola Watchdog — keeps runner.py alive, handles restart requests
# Usage: bash daemon/watchdog.sh
# Run this from /home/vola

set -euo pipefail
VOLA_HOME="$(cd "$(dirname "$0")/.." && pwd)"
cd "$VOLA_HOME"

LOG="$VOLA_HOME/logs/watchdog.log"
mkdir -p logs

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== Vola Watchdog starting (PID $$) ==="
log "Home: $VOLA_HOME"

# Find python
PYTHON="${VOLA_HOME}/daemon/venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
    PYTHON="$(which python3)"
fi
log "Python: $PYTHON"

while true; do
    log "Starting runner..."
    "$PYTHON" daemon/runner.py 2>&1 | tee -a logs/runner.log || true
    EXIT_CODE=$?
    log "Runner exited (code $EXIT_CODE)"

    # Check for permanent shutdown
    if [ -f state/shutdown_permanent.flag ]; then
        log "Permanent shutdown requested — watchdog exiting"
        rm -f state/shutdown_permanent.flag
        break
    fi

    log "Restarting in 2s..."
    sleep 2
done

log "=== Watchdog stopped ==="
