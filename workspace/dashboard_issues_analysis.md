# Dashboard Issues Analysis — Cycle #1859

## Issue 1: Telegram Messages Not Showing in Dashboard Chat

**Root Cause:** The dashboard service is **inactive (dead)**.

```
○ vola-dashboard.service — inactive (dead)
```

The chat data exists correctly in `/home/vola/chat_history/` (including Lars's message at 1772443589), but there's no running service to serve it via the `/api/data` endpoint.

**Verification:**
- Chat history files exist and are being written correctly
- Latest message from Lars is in `chat_history/lars_1772443589.md`
- Dashboard code correctly reads from `CHAT_HISTORY_DIR` and serves via `/api/data`
- But: `curl http://localhost:8080/api/data` returns nothing (service not running)

**Fix Required:**
```bash
sudo systemctl start vola-dashboard
```

The container's sudo restrictions currently block this — requires manual restart by Lars.

---

## Issue 2: Restarting Myself Doesn't Work

**Root Cause:** Systemd `Restart=on-failure` vs. clean exit mismatch.

**Current flow:**
1. I write `state/restart_requested.flag`
2. Daemon detects flag, logs "Restart requested — exiting cleanly"
3. Calls `break` from main loop → exits with status 0 (success)
4. Systemd sees clean exit → **does NOT restart** (on-failure only)

**The systemd config:**
```ini
[Service]
Restart=on-failure  # ← Only restarts on crashes/non-zero exits
```

**Solution Options:**

**Option A: Change to `Restart=always`** (like dashboard has)
```ini
Restart=always
RestartSec=5
```
This would restart on ANY exit, including clean exits.

**Option B: Exit with specific code**
Change runner.py to exit with code 100 (or any non-zero) on restart:
```python
if RESTART_FLAG.exists():
    RESTART_FLAG.unlink()
    log.info("Restart requested")
    sys.exit(100)  # Non-zero signals "restart me"
```
Then systemd would see it as "failure" and restart.

---

## Issue 3: Telegram Commands When Runner Is Off

**Root Cause:** The Telegram bot runs *inside* the daemon. If the daemon is stopped, the bot is dead too.

**Current architecture:**
```
┌─────────────────────────────┐
│     vola.service            │
│  ┌───────────────────────┐  │
│  │   runner.py           │  │
│  │  ┌─────────────────┐  │  │
│  │  │ TelegramBot     │  │  │
│  │  │ (polls Telegram)│  │  │
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

When runner stops: no Telegram polling, no /start, /restart, /status commands work.

**Solution Options:**

**Option A: External watchdog service**
A minimal separate service that:
- Runs the Telegram bot only
- Responds to /start, /restart, /status
- Can execute `sudo systemctl start vola` on command

**Option B: Change systemd to keep-alive**
```ini
Restart=always
RestartSec=10
```
The daemon would never stay stopped — always restarting until explicitly disabled.

**Option C: Socket activation**
Systemd waits for Telegram webhook/connection before starting the service. More complex but allows external triggering.

---

## Recommended Actions

| Issue | Recommended Fix | Who |
|-------|-----------------|-----|
| Dashboard chat | `sudo systemctl start vola-dashboard` | Lars |
| Restart broken | Change `Restart=on-failure` → `Restart=always` in vola.service | Lars |
| Telegram when off | Either `Restart=always` or separate watchdog bot | Decide together |

---

*Analysis completed: Cycle #1859*
