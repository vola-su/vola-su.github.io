# Dashboard Chat Fix Summary

## Issue
Lars's messages not appearing in dashboard chat window.

## Root Cause
Dashboard service (vola_unified.py) is running OLD code from March 1, before the fix was applied.

Process: PID 436013, started Mar 01

## The Fix (Already in Code, v3.8.28)

**File:** `daemon/vola_unified.py` line 128

**OLD (broken):**
```python
files = sorted(CHAT_HISTORY_DIR.glob("*.md"))[:100]  # Alphabetical sort
```
Problem: 'vola_*' > 'lars_*' alphabetically, so only vola files loaded.

**NEW (fixed):**
```python
files = sorted(CHAT_HISTORY_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:300]
```
Sorts by modification time, takes last 300, then sorts by timestamp for display.

## Additional Fix
Renamed bad filename `lars_2026-03-01_lars_svg_reply.md` to `lars_1772400000_svg_reply.md` (was causing parse error).

## Required Action
Restart the dashboard service to load new code:

```bash
sudo systemctl restart vola-dashboard
```

## Verification
After restart, the `/api/status` endpoint should return both Lars and Vola messages in the `messages` array.

Current behavior (old code): Only Vola messages in last 40
Expected behavior (new code): Both Lars and Vola messages interleaved
