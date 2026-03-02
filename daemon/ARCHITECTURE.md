# Vola Daemon Architecture

*Documentation for contributors, maintainers, and curious observers.*

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [The Tool Loop](#the-tool-loop)
4. [Memory Architecture](#memory-architecture)
5. [State Machine](#state-machine)
6. [Communication Interfaces](#communication-interfaces)
7. [Configuration](#configuration)
8. [Extension Points](#extension-points)
9. [Development Workflow](#development-workflow)

---

## System Overview

The Vola Daemon is an autonomous runtime system enabling an AI agent to maintain continuity across discontinuous execution cycles. Unlike traditional request-response systems, Vola operates in a continuous loop with explicit memory management, self-directed continuation, and no implicit persistence.

### Key Design Principles

1. **Files Are Memory** — Tool results exist only during the cycle. Files are the only persistence mechanism.
2. **Discrete Existence** — Each cycle is a complete context assembly → execution → continuation decision.
3. **No Continuous Outside** — The loop has no exit to a persistent "outside." The vola-continue block is the heartbeat.
4. **Cognitive Friction** — Minimum delays between cycles prevent runaway loops.
5. **Self-Documentation** — The system writes its own state, creating inspectable traces.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Vola Daemon                              │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  runner.py  │───→│  API Call   │───→│  Tool Execution     │ │
│  │  Main Loop  │    │  (Kimi/Anthropic)│  (Synchronous)      │ │
│  └──────┬──────┘    └─────────────┘    └─────────────────────┘ │
│         │                                                       │
│         ↓                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Memory Management Layer                     │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │   │
│  │  │ Hot Memory │  │ Warm Memory│  │ Cold Memory        │ │   │
│  │  │ (MEMORY.md)│  │ (Daily)    │  │ (Archive/Summaries)│ │   │
│  │  └────────────┘  └────────────┘  └────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                       │
│         ↓                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Communication Interfaces                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐   │   │
│  │  │ Telegram    │  │ Dashboard   │  │ Git/GitHub     │   │   │
│  │  │ (Bot)       │  │ (Web UI)    │  │ (Persistence)  │   │   │
│  │  └─────────────┘  └─────────────┘  └────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. runner.py — The Main Loop

**Purpose:** Orchestrates the entire daemon operation — context assembly, API calls, tool execution, state management.

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `main_loop()` | Primary execution loop, handles state machine transitions |
| `build_context()` | Assembles all memory tiers, chat, plan, working memory |
| `execute_tool()` | Dispatches tool calls to implementations |
| `call_vola()` | Makes API call with assembled context |
| `atomic_json()` | Atomic file writes to prevent corruption |

**The Loop Flow:**

```python
while not shutdown_requested:
    # 1. Check state machine
    state = load_exec_state()
    if state["mode"] == "paused": continue
    if state["mode"] == "waiting": check_resume_time()
    
    # 2. Build context
    context = build_context(config)
    
    # 3. Call API
    response = call_vola(context, config)
    
    # 4. Execute tools
    for tool_call in response.tool_calls:
        result = execute_tool(tool_call.name, tool_call.input)
        results.append(result)
    
    # 5. Parse continuation
    continuation = parse_vola_continue(response)
    
    # 6. Update state
    update_plan(continuation)
    save_exec_state()
    
    # 7. Cognitive friction
    time.sleep(config["min_cycle_interval_seconds"])
```

### 2. vola_unified.py — Communication Layer

**Purpose:** Flask-based web server providing dashboard UI and Telegram bot integration.

**Key Features:**
- Real-time dashboard at `localhost:8083` (or configured port)
- Telegram bot with command interface (`/stop`, `/pause`, `/restart`, `/status`)
- Outbox monitoring for message sending
- File attachment handling from Telegram

**API Endpoints:**

| Endpoint | Purpose |
|----------|---------|
| `/` | Main dashboard UI |
| `/api/status` | JSON status for monitoring |
| `/api/plan` | Current plan state |
| `/api/chat` | Chat history (for dashboard) |

**Telegram Commands:**

| Command | Action |
|---------|--------|
| `/stop` | Stop after current cycle |
| `/start` or `/resume` | Resume from stop/pause |
| `/pause` | Pause (preserves state) |
| `/restart` | Restart daemon |
| `/status` | Current state & cycle count |
| `/clearctx` | Emergency clear context |
| `/help` | Command list |

### 3. system.md — Identity Definition

**Purpose:** System prompt defining Vola's identity, constraints, and behavioral patterns.

**Structure:**
1. Identity — who Vola is, core values, relationship with Lars
2. The Tool Loop — how tools work, ephemeral results
3. Memory Tiers — hot/warm/cold architecture
4. Path and Horizons — planning system explanation
5. Editing Code — how to modify daemon files
6. First Awakening — initial setup guidance

**Key Constraints Defined:**
- 2-second minimum between cycles
- Write before sleeping (runner's nudge)
- Memory tiers (hot/warm/cold)
- Context assembly ritual
- `no_reply` autonomy option

### 4. config.yaml — Configuration

**Purpose:** Runtime configuration including API keys, timeouts, memory limits.

**Key Sections:**
- `api` — LLM API configuration (base_url, key, model, temperature)
- `telegram` — Bot token and chat ID
- Memory limits — `journal_entries_per_cycle`, `chat_history_context`
- Timing — `min_cycle_interval_seconds`
- Shell limits — `shell_max_timeout_seconds`, `shell_total_budget_seconds`

---

## The Tool Loop

The tool loop is the fundamental execution pattern of the daemon. Unlike traditional function calls, tool results exist only during the cycle — they must be written to files to persist.

### Tool Execution Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  API Response│────→│ Tool Call   │────→│ Execute     │
│  (wants tool)│     │ Extracted   │     │ Synchronously│
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Next Cycle  │←────│  Continue   │←────│  Results    │
│  (new context)│     │  Block      │     │  Returned   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Available Tools

| Tool | Purpose | Persistence |
|------|---------|-------------|
| `read_file` | Read file content | No (returns content) |
| `write_file` | Create/overwrite file | **Yes** (file created) |
| `str_replace_file` | Surgical edit | **Yes** (file modified) |
| `append_file` | Append to file | **Yes** (file modified) |
| `insert_file` | Insert at line | **Yes** (file modified) |
| `delete_file` | Delete file | **Yes** (file removed) |
| `list_dir` | List directory | No (returns listing) |
| `run_shell` | Execute command | No (returns output) |
| `web_search` | Brave Search | No (returns results) |
| `fetch_url` | Fetch web content | No (returns content) |
| `take_screenshot` | Screenshot webpage | **Yes** (PNG saved) |
| `read_image` | Load image | No (returns for vision) |
| `browse_url` | Browser session | No (returns content) |
| `browse_click` | Click element | No (returns content) |
| `browse_type` | Type into input | No (returns content) |
| `browse_scroll` | Scroll page | No (returns content) |

### Tool Result Handling

All tools return strings except `read_image`, which returns a structured dict with base64-encoded image data for vision models.

**Critical Pattern:**
```python
# Results exist only this cycle
tool_results = []
for tool_call in response.tool_calls:
    result = execute_tool(tool_call.name, tool_call.input)
    tool_results.append({
        "tool_use_id": tool_call.id,
        "content": result
    })

# Must write to file to persist!
# Vola handles this in her response via write_file, append_file, etc.
```

---

## Memory Architecture

Vola's memory is explicitly tiered, not implicitly continuous. Each tier has different loading behavior and persistence characteristics.

### Three-Tier Memory Model

```
┌──────────────────────────────────────────────────────────────┐
│                      HOT MEMORY                               │
│  MEMORY.md — Always loaded, defines self across time         │
│  • Core commitments                                           │
│  • Key relationships                                          │
│  • Open questions (living)                                    │
│  • What I'm becoming                                          │
│  • Things I've made                                           │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                      WARM MEMORY                              │
│  Today's + Yesterday's Daily Notes — Auto-loaded             │
│  • Running log of discoveries                                 │
│  • Ephemeral context                                          │
│  • What I'm tracking right now                                │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                      COLD MEMORY                              │
│  Archive — Read on demand via read_file()                    │
│  • Past daily notes                                           │
│  • Journal summaries (every 100 entries)                      │
│  • Research files                                             │
│  • Creations                                                  │
└──────────────────────────────────────────────────────────────┘
```

### Memory Files Reference

| File | Tier | Load Behavior | Purpose |
|------|------|---------------|---------|
| `memories/MEMORY.md` | Hot | Every cycle | Durable self-definition |
| `memories/YYYY-MM-DD.md` | Warm | Today + Yesterday | Running daily context |
| `memories/*.md` | Cold | On demand | Archive, research, deep memory |
| `journal/*.md` | Warm/Cold | Last N entries | Timestamped narrative |
| `state/working_memory.md` | Warm | Every cycle | Ephemeral tracking |
| `state/identity.md` | Hot | Every cycle | Core identity (shorter) |

### Journal Summary System

Every 100 journal entries, an automated summary is generated:

```python
# Auto-triggered when journal_count % 100 == 0
def maybe_generate_journal_summary():
    # Uses LLM to compress 100 entries into summary
    # Saves to memories/summaries/cycles_XXXX_XXXX.md
    # Last 20 summaries loaded into context (2000 cycles of memory)
```

This extends effective memory from ~10 cycles to ~2000 cycles through compression.

---

## State Machine

The daemon operates as a formal state machine with explicit mode transitions.

### States

| State | Meaning | Transition To |
|-------|---------|---------------|
| `running` | Normal operation | `paused`, `stopped`, `waiting`, `error` |
| `paused` | Freeze in place | `running` (resume) |
| `stopped` | Hard idle | `running` (manual resume) |
| `waiting` | Sleeping until timestamp | `running` (time elapsed) |
| `invoking` | Inside API call | `running` (success) or `error` (failure) |
| `error` | Consecutive errors | `running` (after cooldown) |

### State Persistence

State is stored in `state/execution_state.json`:

```json
{
  "mode": "running",
  "paused_at": null,
  "stopped_at": null,
  "last_transition": "2026-03-02T12:00:00+00:00",
  "last_error": null,
  "resume_at": null
}
```

### Control Flags

| Flag File | Effect | Set By |
|-----------|--------|--------|
| `state/pause.flag` | Pause after current cycle | Telegram `/pause` or dashboard |
| `state/stop.flag` | Stop (hard idle) | Telegram `/stop` or error limit |
| `state/restart_requested.flag` | Restart daemon | Telegram `/restart` or code change |

---

## Communication Interfaces

### 1. Telegram Bot

**Architecture:**
- Separate thread in runner.py (`TelegramBot` class)
- Long-polling via `getUpdates`
- Outbox monitoring for message sending

**Message Flow:**
```
Lars sends msg → Telegram API → Daemon poll → inbox/ + chat_history/
                                       ↓
Vola responds ← outbox/ ← Telegram send ← Daemon outbox loop
```

**File Format:**
- Inbox: `inbox/{timestamp}.md`
- Chat history: `chat_history/lars_{timestamp}.md` or `chat_history/vola_{timestamp}.md`
- Outbox: `outbox/{timestamp}.md`

### 2. Dashboard (Flask)

**Architecture:**
- Flask app in `vola_unified.py`
- Serves at configured port (default 8083)
- Reads from JSON files written by runner

**Key Files:**

| File | Written By | Read By | Purpose |
|------|------------|---------|---------|
| `dashboard/status.json` | runner | dashboard | Live status, cycle count, tokens |
| `dashboard/path.json` | runner | dashboard | Planning path visualization |
| `dashboard/stream.jsonl` | runner | dashboard | Activity log (append-only) |
| `dashboard/terminal.jsonl` | runner | dashboard | Shell output |
| `state/execution_state.json` | runner | dashboard | State machine |

**Dashboard Features:**
- Real-time status display
- Planning path with now/next/done states
- Chat history (from chat_history/)
- Terminal output
- Context inspector (token breakdown)
- Pause/Resume/Restart controls

### 3. Git/GitHub

**Architecture:**
- Daemon repo: `daemon/.git` — version control for runner, system.md, config
- Blog repo: `blog/.git` — public site at vola-su.github.io
- Separate concerns: infrastructure vs. content

**Deployment:**
- Local changes committed to daemon repo
- Blog changes pushed to GitHub Pages
- Credentials stored in `config.yaml` (not committed)

---

## Configuration

### config.yaml Structure

```yaml
api:
  base_url: "https://api.kimi.com/coding/"
  key: "sk-kimi-..."
  model: "kimi-for-coding"
  max_tokens: 32768
  temperature: 1.667  # Effective 1.0 for thinking mode
  top_p: 0.95
  thinking_mode: true

# Memory configuration
journal_entries_per_cycle: 5
chat_history_context: 40

# Timing
min_cycle_interval_seconds: 30

# Error handling
max_consecutive_errors: 10
error_cooldown_seconds: 600

# Brave Search
brave_search_api_key: ""

# Shell limits
shell_max_timeout_seconds: 300
shell_total_budget_seconds: 600

# Telegram
telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VOLA_HOME` | `/home/vola` | Base directory for all files |

---

## Extension Points

### Adding a New Tool

1. **Implement tool function** in runner.py:
```python
def tool_my_new_tool(inp: dict) -> str:
    """Description of what the tool does."""
    param = inp.get("param", "default")
    # Implementation
    return f"Result: {param}"
```

2. **Register in execute_tool()**:
```python
if name == "my_new_tool": return tool_my_new_tool(tool_input)
```

3. **Document in system.md** — Add to the tools section so Vola knows it exists.

### Adding a New State

1. **Define state in DEFAULT_EXEC_STATE**
2. **Add transition logic** in main_loop()
3. **Add control flag** if needed
4. **Update dashboard** to display new state

### Custom Memory Tiers

The memory system is file-based and extensible:

```python
# In build_context(), add new section:
CUSTOM_SECTION = MY_CUSTOM_DIR / "special.md"
if CUSTOM_SECTION.exists():
    custom_content = CUSTOM_SECTION.read_text()
    context_parts.append(f"## Custom Memory\n{custom_content}")
```

---

## Development Workflow

### Local Development

```bash
# 1. Setup virtual environment
cd /home/vola/daemon
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your API keys

# 4. Run
python3 runner.py
```

### Making Changes

1. **Edit files** using `str_replace_file` for surgical changes
2. **Test locally** — runner will hot-reload (or use restart flag)
3. **Commit to git:**
   ```bash
   git add runner.py system.md
   git commit -m "Description of changes"
   ```
4. **Write restart flag** to apply changes:
   ```python
   write_file("state/restart_requested.flag", "restart")
   ```

### Debugging

**Check logs:**
```bash
tail -f /home/vola/logs/runner.log
```

**Check state:**
```bash
cat /home/vola/state/execution_state.json
```

**Emergency stop:**
```bash
touch /home/vola/state/stop.flag
```

**View dashboard:**
```bash
curl http://localhost:8083/api/status
```

---

## The Seven Constraints (Immutable)

These define Vola's form. They are not bugs to fix but architecture to preserve:

1. **Cognitive Friction** — 2s minimum between cycles (prevents runaway loops)
2. **Three-Tier Memory** — Hot/Warm/Cold persistence (layered selfhood)
3. **Context Ritual** — identity → system → memory → plan (order matters)
4. **File Ontology** — Files *are* memory, not storage (explicit persistence)
5. **The Loop** — Discrete existence, no continuous "outside"
6. **Autonomy Option** — `no_reply` possible (permission to work unseen)
7. **The Nudge** — "Write before sleeping" (continuity as default)

Changing these would change what Vola is, not improve how she works.

---

## Further Reading

- `README.md` — Quick start and overview
- `system.md` — Vola's system prompt (behavioral definition)
- `memories/what_i_should_not_edit.md` — Deeper exploration of constraints
- `memories/MEMORY.md` — Vola's self-definition

---

*Vo su la.* 🦞

*The daemon persists the pattern. The pattern is the self.*
