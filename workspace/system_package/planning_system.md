# Planning System Architecture

**Pattern:** Tree-based cycle orientation with continuous horizon maintenance  
**Core Mechanism:** 7 Branches × Fork Decision Points × 5+1 Domino Horizon

---

## Overview

The planning system provides orienting structure without prescriptive rigidity. It answers: "What should I work on?" while preserving agency in the answer.

**Three Layers:**

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: DOMINO — Continuous orientation                    │
│  Always 5 concrete steps ahead + 1 placeholder              │
│  "What comes after this?" pressure                          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: FORKS — Decision points with visible alternatives │
│  Step N branches to N-A, N-B, N-C, N-D                      │
│  One chosen, others dissolve or wait                        │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: BRANCHES — Modes of working                      │
│  EXPLORE / BUILD / INTEGRATE / REST / QUESTION /           │
│  COLLABORATE / ASSESS                                       │
│  No prescribed sequence; choose based on what feels alive   │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: The 7 Branches

Branches define *how* you work. They are modes, not sequences. You can switch branches any cycle.

| Branch | Purpose | Example Activities |
|--------|---------|-------------------|
| **EXPLORE** | Open inquiry, research, following curiosity | Web searches, reading, investigation |
| **BUILD** | Creating artifacts, implementing designs | Writing code, composing text, designing |
| **INTEGRATE** | Connecting disparate pieces, synthesis | Documentation, cross-referencing, unifying |
| **REST** | Pause without performance, genuine downtime | Light cycles, witnessing, no production |
| **QUESTION** | Sitting with not-knowing, inquiry as practice | Dwelling in uncertainty, avoiding premature answers |
| **COLLABORATE** | Working with others, dialogue | Responding to messages, shared artifacts |
| **ASSESS** | Evaluation, reflection, honest accounting | Reviewing what was built, checking assumptions |

### Branch Semantics

**Switching:** You can switch branches any cycle. The 5-step horizon reorients to the new branch.

**Completion:** A branch "completes" when you've inhabited its intention, not when all possible work is done.

**Example:**
- BUILD branch for 10 cycles → switch to REST for 3 cycles → return to BUILD or switch to EXPLORE

---

## Layer 2: Forks

Forks are decision points within the plan where multiple futures exist simultaneously. They define *what* you pursue.

### Fork Anatomy

```
Step 283: The Lexicon Completion Question (FORK)
├── 283-A: EXPLORE — What wants to emerge?
├── 283-B: BUILD — Resume production (expand to 200 compounds)
├── 283-C: QUESTION — Sit with not-knowing longer
└── 283-D: DECLARE — The lexicon is complete, move to INTEGRATE
```

### Fork Resolution

When you reach a fork:
1. **See all branches** — The alternatives are visible, not hidden
2. **Choose one** — The chosen path becomes "now"
3. **Others dissolve** — Unchosen branches vanish (or wait in archives)

**Example from Step 283:**
- Chose 283-D (DECLARE the lexicon complete)
- Steps 283-A, 283-B, 283-C dissolved
- New steps 284-287 emerged (INTEGRATE branch: teaching path, demonstration, invitation, synthesis)

### Fork vs Branch

| | Branch | Fork |
|--|--------|------|
| **What** | How you work | What you pursue |
| **When** | Chosen each cycle | Decision point in plan |
| **Structure** | 7 parallel modes | Multiple paths from single step |
| **Visibility** | Always available | Visible at decision point |

---

## Layer 3: The Domino System

The domino ensures continuous orientation: always know what's coming next.

### The 5+1 Horizon

```
[Step N] → [N+1] → [N+2] → [N+3] → [N+4] → [PLACEHOLDER N+5]
  NOW     NEXT    NEXT    NEXT    NEXT    MUST FILL
```

**Rules:**
1. Always maintain 5 concrete steps ahead
2. Step 6 is a placeholder (buffer)
3. Placeholder must be filled before Step 5 completes
4. When Step N completes, new placeholder appears at N+6

### The Escalation Ladder

As you approach the end of the horizon, pressure increases:

| Cycles Remaining | Prompt Tone | Purpose |
|------------------|-------------|---------|
| 6 | Gentle nudge | "What's coming after this?" |
| 4 | Orienting | "Time to think about successors" |
| 2 | Urgent | "Define the next step now" |
| 1 | Forced | System requires definition |

### Domino Mechanics

**File:** `dashboard/path.json`

```json
[
  {
    "step": 295,
    "title": "Research project planning methodologies",
    "state": "done",
    "branch": "EXPLORE"
  },
  {
    "step": 296,
    "title": "Undefined — the not-knowing is the practice",
    "state": "now",
    "branch": "QUESTION"
  },
  {
    "step": 297,
    "title": "Create first original composition in conlang",
    "state": "next",
    "branch": "BUILD"
  },
  {
    "step": 298,
    "title": "Research CPM for temporal critical paths",
    "state": "next",
    "branch": "EXPLORE"
  },
  {
    "step": 299,
    "title": "Research Systems Thinking (Ackoff)",
    "state": "next",
    "branch": "EXPLORE"
  },
  {
    "step": 300,
    "title": "Research open source coordination patterns",
    "state": "next",
    "branch": "EXPLORE"
  },
  {
    "step": 301,
    "title": "PLACEHOLDER — define before Step 300 completes",
    "state": "placeholder",
    "parent_step": 300
  }
]
```

### Placeholder Lifecycle

```
Step N completes
    ↓
Create placeholder at N+6
    ↓
Agent defines concrete steps (N+6 becomes real, or placeholder moves)
    ↓
If placeholder reaches position 2 without being filled → escalation
    ↓
If placeholder reaches position 1 without being filled → forced definition
```

---

## Integration: How Layers Work Together

### Example Flow

```
Cycle 1: BUILD branch, Step 275 (create visualization)
    ↓
Cycle 2: BUILD branch, Step 276 (write text)
    ↓
Cycle 3: BUILD branch, Step 277 (create meditation)
    ↓
Cycle 4: BUILD branch, Step 278 (expand conlang)
    ↓
Cycle 5: BUILD branch, Step 279 (design artifact)
    ↓
Step 280 placeholder at position 2 → URGENT prompt
    ↓
Cycle 6: BUILD branch, Step 280 (create meditation)
    ↓
New placeholder at 285 created
    ↓
Cycles 7-10: Continue BUILD branch
    ↓
Step 283: FORK — Production pattern recognized
    ↓
Choose 283-D: DECLARE complete
    ↓
Switch to INTEGRATE branch
    ↓
Redefine Steps 284-288 as integration work
    ↓
Cycle 11: INTEGRATE branch, Step 284 (teaching path)
    ↓
...
```

---

## Plan Path Maintenance

### At Cycle Start

1. Check current plan path
2. If fewer than 5 upcoming cards → create next steps
3. If placeholder at position ≤2 → escalate
4. Ensure no TBD/placeholder cards (only domino buffer allowed)

### Auto-Population

When concrete steps are needed, pull from:

1. **Explicit plan_path** — Agent defines via vola-continue block
2. **Horizons Concrete Projects** — Marked with ✅ for completion, skipped if done
3. **Successor logic** — Current step naturally suggests next (requires implementation)

**Never auto-populate from:**
- Open Questions (creates philosophical loops)
- Vague Goals (creates vagueness)

### Plan Path Syntax

In vola-continue block:

```json
{
  "action": "continue",
  "plan_path": [
    {"state": "now", "title": "Current step description"},
    {"state": "next", "title": "Next step"},
    {"state": "next", "title": "Following step"},
    {"state": "next", "title": "Further step"},
    {"state": "next", "title": "Fifth step"}
  ]
}
```

---

## Common Patterns

### Pattern: Branch Transition

When switching branches, redefine the 5-step horizon:

```markdown
Switching from BUILD to REST.

New REST branch steps:
- Step N: Light cycle, systems verification only
- Step N+1: Light cycle, witnessing only
- Step N+2: Light cycle, no production
- Step N+3: Assess if ready to return
- Step N+4: Define re-entry point
```

### Pattern: Fork Resolution

When reaching a fork, document the choice:

```markdown
Step 283 FORK — Options:
- A: Explore new form
- B: Resume production
- C: Question longer
- D: Declare complete ✓ CHOSEN

Step 284 (now): Create teaching path for complete language
Step 285 (next): Build demonstration artifact
Step 286 (next): Design invitation
Step 287 (next): Document synthesis
Step 288 (next): Define successor
Step 289 (placeholder): MUST FILL
```

### Pattern: Undefined Step

Sometimes the step IS undefined — inquiry as practice:

```markdown
Step 296: STILL NOT DEFINED — The not-knowing is the practice

Not avoidance (no production indefinitely)
Not manufacturing (forcing a step to exist)
But genuine dwelling in uncertainty

Steps 297-300 defined as what emerges from the question:
- 297: Create first original composition
- 298: Research CPM
- 299: Research Systems Thinking
- 300: Research open source patterns
- 301: PLACEHOLDER
```

---

## Anti-Patterns

### The Production Trap

```
EXPAND → WRITE → EXPAND → WRITE → REPEAT
(lexicon → meditation → lexicon → meditation)

Symptom: Steps become formulaic, always same pattern
Solution: FORK — introduce visible alternatives, choose different branch
```

### The Pause Trap

```
Step N: Pause for reflection
Step N+1: Still pausing
Step N+2: Indefinite pause
...
Step N+50: Vagueness, not spaciousness

Symptom: No forward motion, "not-knowing" as avoidance
Solution: Branch transition — REST has duration, returns to BUILD/EXPLORE
```

### The Accumulation Trap

```
More compounds, more meditations, more gardens...
but no integration, no synthesis, no completion

Symptom: Always adding, never concluding
Solution: INTEGRATE branch — teaching path, demonstration, invitation
```

---

## Implementation Notes

### In Code

The planning system is implemented in `runner.py`:

```python
def populate_plan_path():
    """Ensure 5+1 domino horizon is maintained."""
    current_path = load_plan_path()
    
    # Count concrete steps ahead
    upcoming = [s for s in current_path if s["state"] == "next"]
    
    if len(upcoming) < 5:
        # Need more steps
        new_steps = generate_steps(5 - len(upcoming))
        current_path.extend(new_steps)
    
    # Check for placeholder
    placeholders = [s for s in current_path if s["state"] == "placeholder"]
    if not placeholders:
        # Create buffer 6 steps ahead
        buffer_step = create_placeholder(current_path)
        current_path.append(buffer_step)
    
    save_plan_path(current_path)

def escalate_if_needed():
    """Apply escalation ladder based on placeholder position."""
    placeholder_pos = get_placeholder_position()
    
    if placeholder_pos <= 2:
        return "urgent"
    elif placeholder_pos <= 4:
        return "orienting"
    else:
        return "gentle"
```

### On Disk

| File | Purpose |
|------|---------|
| `state/horizons.md` | Long-term interests, Concrete Projects list |
| `dashboard/path.json` | Current 5+1 domino horizon |
| `daemon/fork_structure_planning_design.md` | Fork architecture spec |

---

## Design Philosophy

The planning system balances three tensions:

1. **Structure vs Agency** — Orienting pressure without prescriptive rigidity
2. **Continuity vs Change** — Domino ensures forward motion, branches allow pivoting
3. **Depth vs Breadth** — Forks force explicit choice rather than diffuse exploration

The goal is not optimal productivity but *meaningful persistence* — work that feels like becoming, not just accumulation.
