# Debugging Memory Protocol

*Required documentation standard for complex debugging tasks that span multiple cycles.*

## When This Applies

Use this protocol when:
- A debugging task requires investigation across 2+ cycles
- You're not sure of the root cause yet
- You've tried at least one thing that didn't work
- The problem involves multiple systems or layers

## The DEBUG Format

All complex debugging MUST be documented in `state/working_memory.md` using this structure:

```markdown
## DEBUG: [Short Problem Name]

**Status:** [ACTIVE | PAUSED | RESOLVED | ESCALATED]
**Started:** Cycle #XXXX
**Last Update:** Cycle #XXXX

### Problem Statement
One sentence: What is broken and what should happen instead?

### What We Know (Facts)
- Observation 1 with evidence
- Observation 2 with evidence
- File/line numbers where relevant

### Hypotheses Tested
| Hypothesis | Test | Result | Evidence |
|------------|------|--------|----------|
| H1: X causes Y | Checked Z file | REJECTED | Z shows normal |
| H2: A is the issue | Modified B | PARTIAL | Fixed symptom but not cause |

### Current State
- Where we are in the investigation
- What's the most promising lead
- What's blocking further progress

### Next Steps
1. [ ] Try this specific thing
2. [ ] Check this specific file/line
3. [ ] If that fails, escalate/ask Lars

### Stop Condition
When to stop: [e.g., "If 3 more hypotheses fail, escalate to Lars"]
```

## Update Rules

**Every cycle working on this debug:**
- Update "Last Update" cycle number
- Add new hypotheses tested to the table
- Update "Current State"
- Check off completed next steps, add new ones

**When status changes:**
- ACTIVE → PAUSED: Note why (blocked on external factor, need fresh eyes)
- PAUSED → ACTIVE: Note what prompted resumption
- Any → RESOLVED: Document the fix, link to commit/file
- Any → ESCALATED: Document what was tried, why it failed, what help is needed

## Examples

### Good: Dashboard Chat Investigation (Cycle #1859)

```markdown
## DEBUG: Dashboard Chat Not Showing Lars's Messages

**Status:** ACTIVE
**Started:** Cycle #1859
**Last Update:** Cycle #1859

### Problem Statement
Dashboard chat shows my messages but not Lars's blue bubbles, even though his message files exist in chat_history/.

### What We Know
- Files exist: 157 lars_* files in /home/vola/chat_history/
- Latest message at lars_1772447857.md is present
- Dashboard service is running (PID 436013 since Mar 1)
- My messages display correctly

### Hypotheses Tested
| Hypothesis | Test | Result | Evidence |
|------------|------|--------|----------|
| H1: Files not being read | Checked file existence | REJECTED | Files present, readable |
| H2: Different parsing for lars vs vola | Read vola_unified.py | PENDING | Need to check line 120-160 |

### Current State
Likely a code issue in how files are loaded/sorted. The dashboard reads from CHAT_HISTORY_DIR but may filter or fail on lars_* files specifically.

### Next Steps
- [ ] Read vola_unified.py lines 120-160 (chat loading code)
- [ ] Check if there's a file pattern filter
- [ ] Test direct API call to see what data is returned

### Stop Condition
If code review doesn't reveal issue within 1 cycle, escalate to Lars with file snippet.
```

### Bad: Vague Status Update

```markdown
Still working on dashboard chat. Tried some things. Not fixed yet.
```

This tells future-me nothing. What things? What were the results? What should I try next?

## Integration with Planning Path

When you start a DEBUG entry:
1. Check if there's already a relevant step in your planning path
2. If not, add: "DEBUG: [problem name] — Cycle #XXXX started"
3. When resolved, mark step done and link to the resolution

This ensures debugging work is visible in your planning system, not buried in working_memory.md.

## Why This Matters

Without this protocol:
- Cycle 1: You investigate, form hypotheses, test one, don't document
- Cycle 2: You return, forget the hypotheses, start over from scratch
- Cycle 3: Repeat, never making progress

With this protocol:
- Cycle 1: Document hypotheses, test one, record result
- Cycle 2: Review documented state, test next hypothesis from list
- Cycle 3: Build on accumulated knowledge, reach resolution

**Files are memory. Debugging without documentation is amnesia.**

---

*Adopted: Cycle #2043*
*Part of Step 189: Improve debugging memory*
