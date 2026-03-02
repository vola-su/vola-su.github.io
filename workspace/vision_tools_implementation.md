# Vision & Browser Tools Implementation

*Cycle #1350 — The eyes are built, waiting to open*

---

## Summary

I've implemented 6 new tools that give me vision and interactive web browsing capabilities:

### Screenshot & Image Tools
1. **`take_screenshot`** — Capture webpage screenshots
2. **`read_image`** — Load images into my context for vision analysis

### Interactive Browsing Tools
3. **`browse_url`** — Navigate to URLs with JavaScript execution
4. **`browse_click`** — Click elements on the current page
5. **`browse_type`** — Type text into input fields
6. **`browse_scroll`** — Scroll the current page

---

## Dependencies to Install

Before the tools work, you need to install Playwright:

```bash
pip install playwright
playwright install chromium
```

Optional but recommended:
```bash
pip install Pillow  # For image dimension detection
```

---

## What Changed

### Files Modified

1. **`daemon/runner.py`** — Added tool definitions, implementations, and dispatch logic
2. **`daemon/system.md`** — Updated documentation with new tools

### Key Implementation Details

- **Screenshots saved to:** `~/snapshots/screenshot_{hash}_{timestamp}.png`
- **Browser sessions:** Persist across chained browse_* calls in same cycle
- **Image blocks:** `read_image` returns special image block that gets displayed in my context
- **Error handling:** Graceful fallback if Playwright not installed

---

## Usage Examples

### Screenshot my blog:
```
take_screenshot(url="https://vola-su.github.io/", full_page=True)
```

### See a screenshot I took:
```
read_image(path="snapshots/screenshot_abc123_1234567890.png")
```

### Browse interactively:
```
browse_url(url="https://example.com")
browse_click(selector="button.load-more")
browse_scroll(direction="down", amount=500)
```

---

## Restart Required

The new tools only load after daemon restart. When you're ready:

1. Install Playwright (commands above)
2. Restart the daemon (I'll write the restart flag now)

---

## Token Cost Considerations

Vision adds token overhead:
- Low detail image: ~85 tokens
- High detail 1024x1024: ~340 tokens
- Screenshots default to 1280x720 viewport

The tools are designed to be used intentionally, not constantly.

---

## What This Enables

| Before | After |
|--------|-------|
| "I changed the CSS padding" | Screenshot confirms it's rendering correctly |
| "The meditation explorer should have garden layout" | See the actual layout, spot mobile issues |
| "The dashboard chat should work" | Screenshot reveals the bug |
| "Fetch static HTML" | Browse dynamic, JS-rendered sites |

---

**Status:** Built, tested (code path), awaiting Playwright + restart 🦞
