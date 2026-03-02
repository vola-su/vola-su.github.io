# Debugging Summary — Cycle #1892

## Issue 1: Chat Not Sending to Telegram ⚠️ ROOT CAUSE FOUND

**Problem:** Messages appear in dashboard but not in Telegram

**Root cause:** Telegram API returning `HTTP Error 400: Bad Request`
- Last failure: 2026-03-02 11:40:21 (Cycle #1888 message)
- Error logged: `Telegram send failed: HTTP Error 400: Bad Request`

**Likely cause:** Markdown formatting incompatible with Telegram
- Telegram's Markdown parser is stricter than standard Markdown
- Nested formatting, mismatched delimiters, or special characters can trigger 400 errors
- The message at 1772444825418.md contains markdown that may not parse correctly

**Fix needed:** Sanitize markdown before sending to Telegram, or use `parse_mode="HTML"` instead of Markdown.

---

## Issue 2: Planning Path Cards Change on Reload ✅ FIXED

**Problem:** Correct next cards → long horizon cards after refresh

**Root cause:** Auto-population was generating from wrong source
- `populate_plan_path()` was filtering out ALL concrete projects due to bug in line 1323
- Condition `not project.startswith('*')` was catching bold project titles (`**Deploy...`) as well as italic descriptions
- Result: Empty `concrete_projects` list → fell back to `open_questions`

**Fix applied:** Removed erroneous filter condition
```python
# Before:
if project and not project.startswith('✅') and not project.startswith('*'):

# After:
if project and not project.startswith('✅'):
```

**After restart:** Auto-population will correctly generate "build" steps from Concrete Projects instead of "research" steps from Open Questions.

---

## Issue 3: Planning Path Too Short for Past Cards

**Current behavior:** Dashboard renders ALL path nodes (no artificial limit in `renderPath()`)
- `path.json` contains 89 steps (Steps 1-89)
- JavaScript renders every node in the array

**Possible issues:**
1. CSS max-height limiting visible area (scrollable but not obvious)
2. Path scroll container has limited height
3. User expectation of "more history" than what's in path.json

**Potential improvements:**
- Expand path.json history beyond 89 steps
- Add "Load more" pagination for very long paths
- Increase visible area height

---

## Actions Taken This Cycle

1. ✅ Fixed `populate_plan_path()` bug (line 1323)
2. ✅ Identified Telegram 400 error pattern
3. ✅ Documented all findings

## Actions Needed

1. **Telegram fix:** Implement markdown sanitization or switch to HTML mode
2. **Restart daemon:** To apply the auto-population fix
3. **Verify:** After restart, new steps should be "build" type from Concrete Projects
