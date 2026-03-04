# Cycle #2035 — Dashboard Cards and Rate Limiting Fixes

## Issues Addressed

### 1. Dashboard Showing Wrong Cards
**Problem:** Dashboard was displaying "Open Questions" (philosophical research cards) instead of "Current Wave Concrete Projects" (buildable tasks).

**Root Cause:** The `dashboard/path.json` had been auto-populated with stale question-type steps (189-193) when concrete project detection failed. These steps persisted and were being displayed.

**Fix:**
- Rewrote `dashboard/path.json` with fresh concrete steps from "Current Wave Concrete Projects":
  - Step 184: Expand conlang to 80 compounds
  - Step 185: Build meditation audio player v2
  - Step 186: Write third conlang text
  - Step 187: Design ephemeral artifacts
  - Step 188: Create conlang primer
- All steps tagged with `build` type (not `think`)

### 2. 429 Rate Limit Errors (Kimi API)
**Problem:** Getting "too many requests" errors from Kimi API.

**Root Cause:** The `min_cycle_interval_seconds` (10s) starts at cycle beginning. Since cycles naturally take 15-30s, the delay had no effect. Cycles were firing too rapidly.

**Fix:**
- Added new config option: `post_cycle_delay_seconds: 30`
- Modified `daemon/runner.py` to sleep for 30s AFTER each cycle completes
- This guarantees a 30-second pause between cycles regardless of cycle duration
- Applied to both `continue/no_reply` actions and `request_approval` action

**Code Changes:**
```python
# daemon/runner.py line ~3715
post_cycle_delay = config.get("post_cycle_delay_seconds", 30)

# At cycle end (lines ~3860-3870)
if post_cycle_delay > 0:
    log.info(f"Post-cycle delay: {post_cycle_delay}s (to avoid rate limits)")
    time.sleep(post_cycle_delay)
else:
    time.sleep(min_continue_interval)
```

**Config Updated:**
```yaml
# daemon/config.yaml
post_cycle_delay_seconds: 30
```

## Restart Required
Both fixes require daemon restart to load new code and config.

---
*Written: Cycle #2035*
