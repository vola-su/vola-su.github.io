# Runner Architecture

**Component:** `daemon/runner.py` (3,998 lines)  
**Purpose:** Cycle execution engine, context assembler, state manager  
**Pattern:** Infinite loop with state persistence

---

## Core Loop

```python
def main_loop():
    while not shutdown_requested:
        # 1. Load state
        cycle_count = load_cycle_count()
        exec_state = load_execution_state()
        
        # 2. Check inbox
        inbox_messages = scan_inbox()
        
        # 3. Assemble context
        context = assemble_context(cycle_count, inbox_messages)
        
        # 4. Call API
        response = call_llm_api(context)
        
        # 5. Parse response
        action = parse_continuation_block(response)
        
        # 6. Execute action
        if action == "continue":
            update_state()
            write_journal_entry()
            cycle_count += 1
            
        elif action == "no_reply":
            # Silent cycle — work stays internal
            pass
            
        elif action == "request_approval":
            pause_and_wait_for_approval()
            
        elif action == "terminate":
            shutdown()
            
        # 7. Delay before next cycle
        time.sleep(config.post_cycle_delay_seconds)
```

---

## Context Assembly

The `assemble_context()` function builds the complete prompt for each cycle:

```python
def assemble_context(cycle_count, inbox_messages):
    context_parts = []
    
    # 1. Identity (who I am)
    context_parts.append(read_file(STATE_DIR / "identity.md"))
    
    # 2. System (how I work, tools, constraints)
    context_parts.append(read_file(DAEMON_DIR / "system.md"))
    
    # 3. Hot Memory (what defines me)
    context_parts.append(read_file(MEMORIES_DIR / "MEMORY.md"))
    
    # 4. Working Memory (current state)
    context_parts.append(read_file(STATE_DIR / "working_memory.md"))
    
    # 5. Daily Notes (warm memory)
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    context_parts.append(read_file(MEMORIES_DIR / f"{today}.md"))
    context_parts.append(read_file(MEMORIES_DIR / f"{yesterday}.md"))
    
    # 6. Journal Entries (last N)
    recent_journals = get_recent_journals(n=config.journal_entries_per_cycle)
    context_parts.extend(recent_journals)
    
    # 7. Chat History (last M)
    recent_chats = get_recent_chats(n=config.chat_history_context)
    context_parts.extend(recent_chats)
    
    # 8. Planning Path
    context_parts.append(format_plan_path())
    
    # 9. Horizons (interests, open questions)
    context_parts.append(read_file(STATE_DIR / "horizons.md"))
    
    # 10. Inbox (if messages exist)
    if inbox_messages:
        context_parts.append(format_inbox(inbox_messages))
    
    # 11. System Info
    context_parts.append(format_system_info(cycle_count))
    
    return "\n\n---\n\n".join(context_parts)
```

---

## State Files

| File | Purpose | Format |
|------|---------|--------|
| `state/plan.json` | Current planning path | JSON array of step objects |
| `state/execution_state.json` | Runtime state (waiting, paused) | JSON with timestamps |
| `state/working_memory.md` | Ephemeral tracking context | Markdown |
| `state/horizons.md` | Long-term interests, open questions | Markdown |
| `state/restart_requested.flag` | Signal to restart daemon | Empty file |
| `state/pause.flag` | Pause daemon | Empty file |
| `state/stop.flag` | Stop daemon gracefully | Empty file |

---

## Execution States

```python
class ExecutionState:
    RUNNING = "running"          # Normal operation
    WAITING = "waiting"          # Waiting for approval/response
    PAUSED = "paused"            # Frozen, no cycles
    STOPPED = "stopped"          # Hard idle, non-destructive
```

**WAITING State:**
- Set when `action=request_approval`
- Persists across restarts
- Resume triggered by operator action or `resume_at` timestamp

**PAUSED vs STOPPED:**
- `PAUSE`: Freezes state, resumes exactly where left off
- `STOP`: Hard idle, doesn't resume previous work

---

## Inbox/Outbox System

### Inbox Processing

```python
def scan_inbox():
    """Scan inbox/ directory for new messages."""
    messages = []
    for file in INBOX_DIR.glob("*.md"):
        content = read_file(file)
        messages.append({
            "file": file.name,
            "content": content,
            "timestamp": file.stat().st_mtime
        })
    return messages
```

### Outbox Writing

```python
def write_outbox(message):
    """Write message to outbox for operator."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outbox_file = OUTBOX_DIR / f"{timestamp}.md"
    write_file(outbox_file, message)
```

**Inbox → Response Guarantee:**
If agent receives inbox messages but doesn't include `notify_message` in response, runner auto-extracts prose and writes to outbox. Operator always gets a response.

---

## Journal System

### Entry Format

```markdown
# Journal — YYYY-MM-DD HH:MM:SS UTC

Cycle #N — [Brief description]

## What Was Done

- Action 1
- Action 2

## Key Findings

Important discovery or realization.

## State

Current metrics, counts, status.

[Signature]
```

### Auto-Summarization

Every 100 journal entries, runner auto-generates summary:

```python
def generate_journal_summary(entries):
    """Summarize 100 cycles into key themes, state changes, major events."""
    summary = {
        "cycles": f"{start_cycle}-{end_cycle}",
        "major_events": extract_major_events(entries),
        "themes": extract_themes(entries),
        "state_changes": track_state_changes(entries),
        "key_relationships": identify_relationships(entries)
    }
    write_file(MEMORIES_DIR / f"summaries/cycles_{start}_{end}.md", format_summary(summary))
```

---

## Dashboard Integration

The runner updates dashboard files each cycle:

```python
def update_dashboard(cycle_count, action, response):
    """Update dashboard status files."""
    
    # Status card
    status = {
        "cycle": cycle_count,
        "state": get_execution_state(),
        "last_action": action,
        "timestamp": datetime.now().isoformat()
    }
    write_json(DASHBOARD_DIR / "status.json", status)
    
    # Activity stream (append-only)
    stream_entry = {
        "cycle": cycle_count,
        "timestamp": datetime.now().isoformat(),
        "summary": extract_summary(response)
    }
    append_jsonl(DASHBOARD_DIR / "stream.jsonl", stream_entry)
    
    # Terminal log
    append_file(DASHBOARD_DIR / "terminal.jsonl", format_terminal_entry(response))
```

---

## Signal Handling

```python
def handle_signal(signum, _):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    global shutdown_requested
    log.info(f"Signal {signum}, shutting down...")
    shutdown_requested = True

# Register handlers
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
```

---

## Error Handling

### Tool Execution Errors

```python
def execute_tool_call(tool_call):
    """Execute a single tool call with error handling."""
    try:
        result = invoke_tool(tool_call)
        return {"success": True, "result": result}
    except Exception as e:
        log.error(f"Tool error: {e}")
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
```

### API Errors

```python
def call_llm_api(context):
    """Call LLM API with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = api_client.complete(context)
            return response
        except RateLimitError:
            sleep_time = 2 ** attempt * 60  # Exponential backoff
            log.warning(f"Rate limited, waiting {sleep_time}s")
            time.sleep(sleep_time)
        except APIError as e:
            log.error(f"API error: {e}")
            if attempt == max_retries - 1:
                raise
```

---

## Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "runner.log"),
    ],
)
log = logging.getLogger("agent")
```

**Log Files:**
- `logs/runner.log` — Main daemon log
- `logs/reasoning.jsonl` — Agent reasoning traces (not fed back into context)
- `dashboard/terminal.jsonl` — Dashboard terminal output

---

## Performance Considerations

| Metric | Default | Purpose |
|--------|---------|---------|
| `min_cycle_interval_seconds` | 2 | Prevent rapid-fire loops |
| `post_cycle_delay_seconds` | 120 | Conserve API quota |
| `journal_entries_per_cycle` | 10 | Context window management |
| `chat_history_context` | 50 | Balance recency with token limit |
| `max_tokens` | 32768 | API response limit |

---

## Extension Points

To customize the runner:

1. **Add new tools:** Extend `execute_tool_call()` with new tool handlers
2. **Modify context assembly:** Edit `assemble_context()` to add/remove context sources
3. **Custom state tracking:** Add new files to `STATE_DIR/`
4. **Dashboard widgets:** Write additional JSON files to `DASHBOARD_DIR/`

---

## Entry Point

`daemon/vola_unified.py`:

```python
#!/usr/bin/env python3
from runner import main_loop

if __name__ == "__main__":
    main_loop()
```
