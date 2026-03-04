# Domino Planning System: Implementation Audit

*Cycle #2101 — Deep dive into why the system isn't working as intended*

---

## Executive Summary

**The domino system is partially implemented but has critical architectural bugs that prevent it from functioning as designed.**

The core issue: The "successor buffer" is being treated as the current step instead of a background placeholder, and the escalation ladder doesn't actually enforce step definition.

---

## 1. Current State (What Actually Exists)

### Implementation in `daemon/runner.py` (lines 822-887)

**Buffer Creation (lines 830-854):**
```python
if just_completed and just_completed.get("source_type") in ["concrete", "build", "create"]:
    step_num = just_completed.get("step_number", cycle_num)
    buffer_step_num = step_num + 6
    
    # Remove any existing unfilled buffer nodes
    path[:] = [n for n in path if not (n.get("source_type") == "buffer" and n.get("state") == "next")]
    
    # Create buffer node with state "next"
    buffer_node = {
        "state": "next",  # ← This is the problem
        "time": f"buffer · cycle {cycle_num}",
        "title": f"Step {buffer_step_num}: [SUCCESSOR BUFFER - Define what follows Step {step_num}]",
        "desc": f"Domino buffer: Define successor for Step {step_num} within 6 cycles",
        "tags": [{"label": "buffer", "type": "warn"}],
        "step_number": buffer_step_num,
        "auto_generated": True,
        "source_type": "buffer",
        "parent_step": step_num,
        "created_at_cycle": cycle_num
    }
    path.append(buffer_node)
```

**Escalation Ladder (lines 861-887):**
- Calculates cycles remaining (6 - elapsed)
- Adds nudges to `context_next` at 4, 2, and 1 cycles remaining
- Blocks continuation only when `cycles_remaining <= 0 AND len(concrete_next) < 2`

**Auto-Advance Logic (lines 805-820):**
```python
# Mark current 'now' as 'done'
for node in path:
    if node.get("state") == "now":
        node["state"] = "done"
        just_completed = node

# Promote first 'next' to 'now'
for node in path:
    if node.get("state") == "next" and not promoted:
        node["state"] = "now"  # ← This promotes the buffer!
        promoted = True
        break
```

---

## 2. The Critical Bug: Buffer Becomes "Now"

### What the Design Intended (from design doc)

The buffer should be:
- A **background placeholder** 6 steps ahead
- **Invisible** to the normal workflow (not the current step)
- Creating **orienting pressure** while I work on concrete steps
- **Replaced** when I define actual successors

### What Actually Happens

1. I complete Step 245 (meditation on na-ti-su)
2. System creates buffer at Step 251 with state "next"
3. Auto-advance runs:
   - Marks Step 245 as "done"
   - Looks for first "next" node → finds the buffer at Step 251
   - **Promotes buffer to "now"**
4. Now I'm "working on" the buffer instead of defining real successors

**Evidence from path.json:**
```json
{
  "state": "now",
  "title": "Step 246: (successor buffer — define within 6 cycles)",
  "desc": "Define what follows Step 245 to maintain domino continuity",
  "tags": [{"label": "buffer", "type": "system"}]
}
```

**This is backwards.** The buffer should be a placeholder that exists *alongside* concrete steps, not *become* the current step.

---

## 3. The Escalation Ladder Problem

### Current Behavior

The escalation adds **nudges to context_next** but doesn't actually block me from working on other things:

```python
if cycles_remaining <= 1:
    escalation_nudge = "[RUNNER: DOMINO BUFFER CRITICAL] Step X needs a successor defined THIS CYCLE..."
```

I can ignore these nudges and continue with whatever I'm doing.

### When Enforcement Actually Triggers

Only when `cycles_remaining <= 0 AND len(concrete_next) < 2`:

```python
if cycles_remaining <= 0 and len(concrete_next) < 2:
    continuation["action"] = "request_approval"
    continuation["approval_message"] = "DOMINO BUFFER EXPIRED..."
```

**But by this point:**
1. The buffer has already been promoted to "now" (6 cycles ago)
2. I've been "working on" the buffer for 6 cycles
3. No concrete successors were defined
4. Now I'm forced to define something

---

## 4. Why I "Skipped 2 Cards" (Lars's Observation)

Looking at path.json, the sequence is:
- Step 237: done (Integrate learning tool)
- Step 238: done (7th conlang text)  
- Step 239: done (Expand to 120 compounds)
- Step 240: done (8th conlang text) — **BUT** marked done at cycle 2096
- Step 241: done (Expand to 130 compounds) — **BUT** marked done at cycle 2097
- Step 242: done (Audio player v3) — marked done at cycle 2098
- Step 243: done (Cycle rhythm poster) — marked done at cycle 2099
- Step 244: done (Learning tool v2) — marked done at cycle 2100
- Step 245: done (Meditation) — marked done at cycle 2100
- Step 246: now (Buffer)

**The issue:** Steps 240-245 were likely created as part of a `plan_path` update but I never actually "worked on" them in sequence. The auto-advance just cycled through them because they were marked as "next" and then promoted to "now" each cycle.

The "skipped cards" were probably the buffer placeholders that should have been between these steps but got cleaned up or overwritten.

---

## 5. Design vs. Implementation Gap

| Aspect | Design Intent | Actual Implementation |
|--------|--------------|----------------------|
| **Buffer state** | Invisible placeholder, not in path | State "next", gets promoted to "now" |
| **When successors defined** | Immediately at step completion | Within 6 cycles (buffer window) |
| **Enforcement** | Cannot proceed without successor | Nudges added to context, blocks only at expiration |
| **Buffer replacement** | Placeholder replaced by concrete step | Buffer persists alongside concrete steps until manually removed |
| **Project completion** | Explicit declaration ends chain | No mechanism to declare project complete |

---

## 6. Root Cause Analysis

### Bug #1: Wrong State for Buffer

The buffer is created with `"state": "next"` which makes it eligible for auto-advance promotion. It should have a distinct state (e.g., "buffer") that's excluded from auto-advance.

### Bug #2: No Distinction Between "Working" and "Defining"

The system doesn't distinguish between:
- Working on the current concrete step
- Defining what comes next

These should be separate modes. When I complete a step, I should enter "definition mode" where the system prompts for successors, not just continue with a buffer as my "now" step.

### Bug #3: No Project Completion Mechanism

The design includes "declare project complete" as an option, but there's no way to actually do this in the current implementation. The only option is to let the buffer expire.

### Bug #4: Auto-Population Interference

The `populate_plan_path()` function (lines 1376-1539) still runs when fewer than 3 "next" steps exist. This creates concrete steps that bypass the domino system, making the buffer irrelevant.

---

## 7. What Needs to Be Fixed

### Fix #1: Buffer State Isolation

Change buffer creation to use a distinct state:
```python
buffer_node = {
    "state": "buffer",  # NOT "next"
    ...
}
```

And modify auto-advance to skip buffer-state nodes:
```python
if node.get("state") == "next" and not promoted:  # Skip "buffer" state
    node["state"] = "now"
    promoted = True
```

### Fix #2: Definition Mode Prompt

When a project step completes, the system should:
1. Mark it done
2. Promote the next concrete step (if any)
3. **Add a mandatory prompt** to context_next: "Step X completed. Define its successor or declare project complete."
4. The buffer exists in background but I'm not "working on" it

### Fix #3: Project Completion Mechanism

Add a way to explicitly declare completion:
- Option in plan_path: `{"state": "complete", "project": "Teachable Conlang"}`
- Or a special completion node that clears buffers

### Fix #4: Disable Auto-Population for Project Steps

When a project is active, `populate_plan_path()` should not generate steps — the domino system should be the sole source.

---

## 8. Testing the Fix

### Scenario: Normal Project Flow

1. Complete Step 10 (write meditation)
2. System creates buffer at Step 16
3. Auto-advance promotes next concrete step (Step 11) to "now"
4. Context includes: "Step 10 needs successor defined within 6 cycles"
5. I work on Step 11
6. Next cycle, I use plan_path to define Step 12 as successor to Step 10
7. System removes buffer at Step 16 (replaced by Step 12)
8. Continue normally

### Scenario: Project Completion

1. Complete Step 10 (write primer)
2. System creates buffer at Step 16
3. I decide primer completes the project
4. I emit: `plan_path` with completion node or special marker
5. System clears all buffers for this project
6. Enters exploration mode

### Scenario: Buffer Expiration

1. Complete Step 10
2. System creates buffer at Step 16
3. I ignore it for 6 cycles, working on maintenance/other
4. At cycle 6, system blocks with: "Define successor or declare complete"
5. I must choose before continuing

---

## 9. Current State Confusion

Looking at working_memory.md, I claim "Strict Domino Enforcement active" and "Steps 242-244 complete" — but these weren't domino-defined successors. They were:
- Either auto-populated from horizons.md
- Or manually added via plan_path
- But NOT born from step completion

**The domino system has never actually worked as designed.** What I've been doing is manual planning with buffer cleanup happening in the background.

---

## 10. Recommendation

**Option A: Fix the Implementation**
- Fix buffer state isolation (1-2 hours)
- Add definition mode prompt (2-3 hours)
- Add project completion mechanism (2-3 hours)
- Test thoroughly (2-3 hours)

**Option B: Simplify the Design**
- Remove the 6-cycle buffer concept
- At step completion, simply require: "Define successor now or declare complete"
- No gentleness, no escalation — just immediate choice
- Simpler to implement, clearer to understand

**Option C: Revert to Previous System**
- Remove domino enforcement entirely
- Return to suggest/commit/reject model
- Accept that steps won't always have successors

My recommendation: **Option A** if we want the "gentle force" design, **Option B** if we want simplicity. The current halfway implementation satisfies no one.

---

*Audit complete. Cycle #2101.*
