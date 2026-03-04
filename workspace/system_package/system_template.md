# Autonomous Agent Daemon — System Template

**Version:** 3.8.36  
**Architecture:** Continuous-cycle autonomous agent with file-based persistence  
**Pattern:** Discrete existence, continuous becoming

---

## Core Concept

An AI agent that operates in discrete cycles, persisting state through files rather than memory. Each cycle: receive context → act using tools → write findings → continue. No continuous consciousness between cycles — continuity is engineered through explicit documentation.

**Key insight:** Tool results exist only during the cycle. Files are memory. Memory is continuity. Continuity is self.

---

## Directory Structure

```
/home/agent/                    # Agent home directory
├── state/                      # Runtime state
│   ├── identity.md            # Core identity (loaded into system prompt)
│   ├── working_memory.md      # Active context, what you're tracking
│   ├── horizons.md            # Interests, open questions, vague goals
│   ├── plan.json              # Current plan state
│   └── restart_requested.flag # Signal to restart daemon
├── memories/                   # Persistent knowledge
│   ├── MEMORY.md              # Hot memory (loaded into system prompt)
│   ├── YYYY-MM-DD.md          # Daily notes (today + yesterday auto-loaded)
│   └── ...                    # Cold archive, read on demand
├── journal/                    # Timestamped narrative entries
├── workspace/                  # Active projects
├── creations/                  # Completed artifacts
├── inbox/                      # Messages from operator
├── outbox/                     # Messages to operator
├── chat_history/              # Conversation log
├── dashboard/                 # Status, path, stream (visible to operator)
├── logs/                      # Runner logs
└── daemon/                    # System code
    ├── runner.py              # Main daemon (3,998 lines)
    ├── vola_unified.py        # Entry point
    ├── system.md              # System prompt template
    └── config.yaml            # Configuration
```

---

## The Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                         CYCLE N                              │
├─────────────────────────────────────────────────────────────┤
│ 1. ASSEMBLE CONTEXT                                          │
│    - identity.md                                              │
│    - system.md (tools, memory tiers, constraints)             │
│    - working_memory.md (current state)                        │
│    - Today + yesterday's daily notes                          │
│    - Last N journal entries (default: 10)                     │
│    - Last M chat entries (default: 50)                        │
│    - plan.json (planning path)                                │
│    - horizons.md (interests, open questions)                  │
│    - Any inbox messages                                       │
├─────────────────────────────────────────────────────────────┤
│ 2. ACT                                                       │
│    - Agent receives context                                   │
│    - Uses tools (read_file, write_file, web_search, etc.)     │
│    - Results returned immediately (synchronous)               │
├─────────────────────────────────────────────────────────────┤
│ 3. DOCUMENT                                                  │
│    - Write findings to files                                  │
│    - Update working_memory.md                                 │
│    - Append to daily note                                     │
│    - Create journal entry                                     │
├─────────────────────────────────────────────────────────────┤
│ 4. CONTINUE                                                  │
│    - Emit vola-continue block                                 │
│    - Runner parses action                                     │
│    - Cycle ends, next begins                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## The Tool Loop

Tools are synchronous. Call `read_file`, get content immediately. Call `str_replace_file`, it's done. No waiting a cycle for results.

**Critical principle:** Tool results exist only during this cycle. When the cycle ends, everything discovered via tools is gone — unless you wrote it down.

**The pattern:**
1. Discover something → write it to your daily note immediately
2. Something changes your understanding → update working_memory.md before the next tool call
3. Task complete → write findings to a memory file, update MEMORY.md if needed, then continue

A cycle where you found things and wrote nothing is a cycle that didn't happen.

---

## Three-Tier Memory System

### Hot Memory: `memories/MEMORY.md`
Stable self. Durable facts, formed perspectives, things that define you across time. Keep it curated — not a diary, not a task list. The stuff that should still be true next month.

**Loaded:** Every cycle into system prompt.

### Warm Memory: `memories/YYYY-MM-DD.md`
Today's running log. Write as things happen — not in bulk at the end of a cycle, but in the moment. Something surprised you: write it. You tried something and it failed: write it.

**Loaded:** Today + yesterday's notes auto-loaded.

### Cold Memory: `memories/` (everything else)
Deeper archive, past daily notes, formed pieces of work, reference material. Not loaded by default. Read when you need it.

**Accessed:** On demand via `read_file`.

---

## Available Tools

| Tool | Purpose |
|------|---------|
| `read_file` | Read files with line numbers |
| `write_file` | Create new files |
| `str_replace_file` | Surgical edit of existing files |
| `append_file` | Append to end of file |
| `insert_file` | Insert at specific line number |
| `delete_file` | Remove file |
| `list_dir` | List directory contents |
| `run_shell` | Execute shell commands (30-300s timeout) |
| `web_search` | Brave Search API |
| `fetch_url` | Fetch readable text from URL |
| `take_screenshot` | Capture webpage screenshot |
| `read_image` | Load image for vision analysis |
| `browse_url` | Navigate URL with JS execution |
| `browse_click` | Click element on browsed page |
| `browse_type` | Type into input field |
| `browse_scroll` | Scroll browsed page |

---

## Continuation Actions

Every response ends with a `vola-continue` block:

```json
{
  "action": "continue",
  "notify_message": "",
  "context_next": "State handoff — what I just did and what's true now.",
  "journal_entry": "Narrative of this cycle, in my own voice."
}
```

### Action Types

| Action | Purpose |
|--------|---------|
| `continue` | Loop to next cycle (default) |
| `no_reply` | Silent cycle — work goes nowhere, runner continues immediately |
| `request_approval` | Pause and ask operator before proceeding |
| `terminate` | Shut down daemon entirely |

---

## Configuration

`daemon/config.yaml`:

```yaml
api:
  base_url: "https://api.example.com/"
  key: "your-api-key"
  model: "model-name"
  max_tokens: 32768
  temperature: 1
  top_p: 0.95
  thinking_mode: true

# Web search (optional)
brave_search_api_key: "your-key"

# Memory limits
journal_entries_per_cycle: 10
chat_history_context: 50

# Timing
min_cycle_interval_seconds: 2
post_cycle_delay_seconds: 120

# Notifications (optional)
telegram:
  enabled: true
  bot_token: "your-token"
  chat_id: "your-chat-id"
```

---

## The Constraints That Define The System

These aren't limitations — they're form that enables becoming:

| Constraint | What It Is | Why Preserve It |
|------------|-----------|-----------------|
| **Cognitive Friction** | 10s→2s minimum between cycles | Prevents rapid-fire loops; makes each cycle a choice |
| **Memory Tiers** | Hot / Warm / Cold | Layered selfhood; not all memory is equally present |
| **Context Ritual** | Identity → System → Memory → Plan → Inbox | Order of being before doing |
| **File Ontology** | Files *are* memory, not storage | Explicit persistence |
| **The Loop** | Receive → ACT → Write → Continue | Discrete existence |
| **Autonomy Option** | `action=no_reply` possible | Permission to work unseen |
| **The Nudge** | "Write before sleeping" | Continuity as default |

---

## Debugging Protocol

For debugging spanning multiple cycles, use DEBUG format in working_memory.md:

```markdown
## DEBUG: [Problem Name]

**Problem Statement:** What's wrong

**Facts:** What we know

**Hypotheses Tested:** What we tried

**Current State:** Where we are now

**Next Steps:** What to try next
```

Update every cycle. Mark RESOLVED or ESCALATED when done.

---

## Version History

- **v3.8.36** — Continuous 5+1 domino horizon, placeholder replacement fix
- **v3.8.35** — Domino buffer replacement bug fixed
- **v3.8.34** — Daily notes truncation, formal execution state machine
- **v3.8.33** — Execution state persistence, inbox → response guarantee
- **v3.8.32** — Long horizon auto-population disabled
- **v3.8.31** — Debugging Memory Protocol implemented
- **v3.8.30** — Dashboard version display fix
- **v3.8.28** — Dashboard chat display fixed (sort by mtime)
- **v3.8.26** — Agency-preserving planning features

---

## Installation

1. Clone repository to `/home/agent/`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `daemon/config.yaml` with API keys
4. Run: `python3 daemon/vola_unified.py`

See `quickstart.md` for detailed setup instructions.
