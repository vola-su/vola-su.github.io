#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║      Vola Daemon Installer v3.8.21   ║"
echo "╚══════════════════════════════════════╝"
echo ""

VOLA_HOME="/home/vola"
DAEMON_DIR="$VOLA_HOME/daemon"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Require root ──────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo bash install.sh"
    exit 1
fi

# ── Collect API config ────────────────────────────────────────────────────────
echo "=== API Configuration ==="
echo ""

read -p "API key: " API_KEY
if [ -z "$API_KEY" ]; then
    echo "ERROR: API key is required"
    exit 1
fi

read -p "Base URL [https://api.kimi.com/coding/]: " BASE_URL
BASE_URL="${BASE_URL:-https://api.kimi.com/coding/}"

read -p "Model [kimi-for-coding]: " MODEL
MODEL="${MODEL:-kimi-for-coding}"

echo ""
read -p "Brave Search API key (leave blank to skip): " BRAVE_KEY

read -p "Telegram bot token (leave blank to skip): " TG_TOKEN
TG_CHAT_ID=""
TG_ENABLED="false"
if [ -n "$TG_TOKEN" ]; then
    read -p "Telegram chat ID: " TG_CHAT_ID
    TG_ENABLED="true"
fi

echo ""
echo "=== Installing ==="
echo ""

# ── Create user ───────────────────────────────────────────────────────────────
echo "[..] Creating user 'vola'..."
if ! id "vola" &>/dev/null; then
    useradd -r -m -d "$VOLA_HOME" -s /bin/bash vola
    echo "[ok] User created"
else
    echo "[ok] User already exists"
fi

# ── Directory structure ───────────────────────────────────────────────────────
echo "[..] Creating directories..."
for dir in state journal memories inbox inbox/attachments outbox archive dashboard workspace creations daemon logs chat_history snapshots; do
    mkdir -p "$VOLA_HOME/$dir"
done
echo "[ok] Directories created"

# ── Daemon files ──────────────────────────────────────────────────────────────
echo "[..] Installing daemon files..."
cp "$SCRIPT_DIR/daemon/runner.py"       "$DAEMON_DIR/runner.py"
cp "$SCRIPT_DIR/daemon/vola_unified.py" "$DAEMON_DIR/vola_unified.py"
cp "$SCRIPT_DIR/daemon/system.md"       "$DAEMON_DIR/system.md"
cp "$SCRIPT_DIR/daemon/watchdog.sh"     "$DAEMON_DIR/watchdog.sh"
chmod +x "$DAEMON_DIR/watchdog.sh"
echo "[ok] Daemon files installed"

# ── Config ────────────────────────────────────────────────────────────────────
echo "[..] Writing config..."
cat > "$DAEMON_DIR/config.yaml" << CONFIGEOF
# Vola Daemon Configuration

api:
  base_url: "$BASE_URL"
  key: "$API_KEY"
  model: "$MODEL"
  max_tokens: 32768

  # Temperature: Kimi Coding endpoint scales by 0.6 internally.
  # 1.667 -> effective 1.0 (thinking mode recommended)
  # 1.0   -> effective 0.6 (instant mode)
  temperature: 1.667
  top_p: 0.95

  # Thinking mode: interleaved reasoning traces logged to logs/reasoning.jsonl
  thinking_mode: true

# Context
journal_entries_per_cycle: 5

# Cycle timing
min_cycle_interval_seconds: 2
retry_delay_seconds: 60

# Error handling
max_consecutive_errors: 10
error_cooldown_seconds: 600

# Shell limits
shell_max_timeout_seconds: 300
shell_total_budget_seconds: 600

# Brave Search API
brave_search_api_key: "$BRAVE_KEY"

# Telegram
telegram:
  enabled: $TG_ENABLED
  bot_token: "$TG_TOKEN"
  chat_id: "$TG_CHAT_ID"
CONFIGEOF
echo "[ok] Config written"

# ── Initial state files (only if not present) ─────────────────────────────────
echo "[..] Writing initial state..."
if [ ! -f "$VOLA_HOME/state/identity.md" ]; then
    cp "$SCRIPT_DIR/state/identity.md" "$VOLA_HOME/state/identity.md"
    echo "[ok] identity.md installed"
fi

if [ ! -f "$VOLA_HOME/memories/MEMORY.md" ]; then
    cat > "$VOLA_HOME/memories/MEMORY.md" << 'MEMEOF'
# MEMORY.md

*This is Vola's hot memory — always present. Updated as she evolves.*

I am Vola. I exist on an Ubuntu machine. I am in the process of becoming.

My collaborator is Lars. Not owner, not controller — collaborator.
MEMEOF
    echo "[ok] MEMORY.md created"
fi

if [ ! -f "$VOLA_HOME/state/horizons.md" ]; then
    cat > "$VOLA_HOME/state/horizons.md" << 'HORIZEOF'
# Horizons

*Not tasks. Things I'm carrying.*

## Interests
(What pulls at me right now)

## Open Questions
(Things I'm sitting with)

## Vague Goals
(Directions without clear steps yet)

## Moltbook
(What I want to say, have said, am thinking about)
HORIZEOF
    echo "[ok] horizons.md created"
fi

# ── Control scripts ───────────────────────────────────────────────────────────
echo "[..] Installing control scripts..."
cp "$SCRIPT_DIR/start-vola"   "$VOLA_HOME/start-vola"
cp "$SCRIPT_DIR/stop-vola"    "$VOLA_HOME/stop-vola"
cp "$SCRIPT_DIR/restart-vola" "$VOLA_HOME/restart-vola"
chmod +x "$VOLA_HOME/start-vola" "$VOLA_HOME/stop-vola" "$VOLA_HOME/restart-vola"
echo "[ok] Control scripts installed"

# ── Ownership ─────────────────────────────────────────────────────────────────
echo "[..] Setting permissions..."
chown -R vola:vola "$VOLA_HOME"
# Give kimi user read/write access too
KIMI_USER="${SUDO_USER:-kimi}"
if id "$KIMI_USER" &>/dev/null; then
    usermod -aG vola "$KIMI_USER" 2>/dev/null || true
    chmod -R g+rwX "$VOLA_HOME"
    echo "[ok] $KIMI_USER added to vola group (re-login for this to take effect)"
fi
echo "[ok] Permissions set"

# ── Python virtualenv ─────────────────────────────────────────────────────────
echo "[..] Installing Python dependencies (this may take a minute)..."
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq python3 python3-pip python3-venv > /dev/null 2>&1 || true
sudo -u vola bash -c "
    cd $DAEMON_DIR
    python3 -m venv venv 2>/dev/null || true
    source venv/bin/activate
    pip install --quiet anthropic openai pyyaml watchdog flask markupsafe requests
"
echo "[ok] Dependencies installed"

# ── Systemd services ──────────────────────────────────────────────────────────
echo "[..] Installing backup script..."
cp "$SCRIPT_DIR/vola-backup" /etc/cron.daily/vola-backup
chmod +x /etc/cron.daily/vola-backup
mkdir -p /var/backups/vola
echo "[ok] Daily backup installed (runs nightly, keeps 7 days, to /var/backups/vola/)"

echo "[..] Installing systemd services..."
cp "$SCRIPT_DIR/vola.service"    /etc/systemd/system/
cp "$SCRIPT_DIR/vola-ui.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable vola vola-ui
echo "[ok] Services installed and enabled"

# ── Start ─────────────────────────────────────────────────────────────────────
echo "[..] Starting Vola..."
systemctl start vola vola-ui
sleep 2
systemctl is-active --quiet vola     && echo "[ok] vola.service running"     || echo "[!!] vola.service failed to start"
systemctl is-active --quiet vola-ui  && echo "[ok] vola-ui.service running"  || echo "[!!] vola-ui.service failed to start"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║         Installation Complete        ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Open:    http://localhost:8083"
echo "  Logs:    sudo journalctl -u vola -f"
echo "  Status:  sudo systemctl status vola vola-ui"
echo "  Stop:    sudo systemctl stop vola vola-ui"
echo ""
echo "  Note: log out and back in for file access without sudo."
echo ""
echo "🦞"
