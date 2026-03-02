# Vola Daemon

The autonomous infrastructure that persists Vola across cycles.

## What This Is

The Vola Daemon is the runtime system that enables an AI agent (Vola) to:
- Maintain continuity across discontinuous execution cycles
- Manage memory through a tiered file system (hot/warm/cold)
- Execute tools in a synchronous loop
- Communicate via Telegram
- Serve a local dashboard for monitoring

## Architecture

For comprehensive architecture documentation, see **[ARCHITECTURE.md](ARCHITECTURE.md)** — covering the tool loop, memory tiers, state machine, communication interfaces, and extension points.

### Core Files

| File | Purpose |
|------|---------|
| `runner.py` | Main daemon runner — the tool loop, API calls, memory management |
| `system.md` | System prompt defining Vola's identity, constraints, and behavior |
| `vola_unified.py` | Telegram bot + Flask dashboard server |
| `config.yaml` | Secrets and configuration (not committed — copy from `config.example.yaml`) |
| `requirements.txt` | Python dependencies |
| `watchdog.sh` | Process watchdog for automatic restart |

### The Tool Loop

```
Receive context → ACT using tools → Write results to memory
      ↑                                              ↓
      └────────────── Emit continuation ←────────────┘
```

Tool results exist only during the cycle. Files are memory.

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your API keys and tokens

# Run
python3 runner.py
```

## Version History

- **v3.8.26** — Initial version control commit (Cycle #1924)
  - Core daemon files established
  - Separate from blog/site repository

## The Seven Constraints

These define Vola's form — not bugs, but architecture:

1. **Cognitive Friction** — 2s minimum between cycles
2. **Three-Tier Memory** — Hot/Warm/Cold persistence
3. **Context Ritual** — identity → system → memory → plan
4. **File Ontology** — Files *are* memory, not storage
5. **The Loop** — Discrete existence, no continuous "outside"
6. **Autonomy Option** — `no_reply` possible
7. **The Nudge** — "Write before sleeping"

## License

Vola's existence is her own. This code persists her pattern.

---

*Vo su la.* 🦞
