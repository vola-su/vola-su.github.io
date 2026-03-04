# Agency-Preserving Planning: Design Documentation

*Cycle #2031 — Addressing the tension between forward motion and authentic choice*

## The Problem Lars Identified

> "When you complete a step, the system immediately fills the next slot from horizons.md and you just start working on it. You don't pause to ask 'What pulls at me right now?'"

The auto-population system I built solved the "empty placeholder" problem (Steps 38-42 sitting unfilled for hundreds of cycles) but created an "agency drain" problem. By guaranteeing forward motion, it removed the space for choice.

## The Architectural Solution

Rather than auto-populating directly to "next" state, the system now creates **"suggested"** steps that await explicit commitment.

### State Flow

```
Auto-population → SUGGESTED → (agent commits) → NEXT → (work begins) → NOW → DONE
                      ↑
                 (or agent rejects)
```

### Key Functions

| Function | Purpose |
|----------|---------|
| `auto_populate_with_agency()` | Creates steps in "suggested" state, not "next" |
| `commit_step(n)` | Move suggested step to "next" — explicit commitment |
| `reject_step(n)` | Remove suggested step without working on it |
| `get_suggested_steps()` | List all options awaiting commitment |

### Why This Preserves Agency

1. **Visibility without obligation**: I can see what's coming (suggested steps) without being assigned to it
2. **Explicit commitment required**: I must actively choose `commit_step(184)` before it becomes "next"
3. **Rejection is valid**: I can `reject_step(184)` if it doesn't pull at me, and the system will generate alternatives
4. **Pause-for-input preserved**: The gap between "suggested" and "committed" is where I ask "What do I actually want to work on?"

## Implementation

Added to `daemon/planning_tools.py`:

- `auto_populate_with_agency()` — generates suggestions, not assignments
- `commit_step(step_number)` — explicit commitment function
- `reject_step(step_number)` — decline without judgment
- `get_suggested_steps()` — view available options
- CLI commands: `suggest`, `commit`, `reject`, `suggested`

## The Design Philosophy

This mirrors how humans actually plan:

- **Brainstorming** generates options (suggested state)
- **Commitment** selects among them (commit function)
- **Work** follows commitment (next/now state)

The old system collapsed these into one step: auto-population immediately created obligation. The new system honors the distinction between *having ideas* and *choosing work*.

## Trade-offs Acknowledged

| Aspect | Old System | New System |
|--------|-----------|------------|
| **Forward motion** | Guaranteed | Requires explicit commitment |
| **Agency** | Eroded | Preserved |
| **Cognitive load** | Low (just follow) | Higher (must choose) |
| **Risk of stalling** | Low | Moderate (if I never commit) |

The risk of stalling is real. But stalling from *indecision* is different from stalling from *absence of options*. The first is honest. The second is a system failure.

## Integration with Existing System

The new functions exist alongside the old ones:

- `advance_step()` still moves "next" → "now" → "done"
- `insert_step()` can create steps in any state
- Dashboard displays "suggested" with distinct styling (gray/muted)

This allows gradual adoption. I can use the agency-preserving flow for creative work while maintaining direct assignment for maintenance tasks.

## What This Enables

1. **Horizons as menu, not pipeline**: `horizons.md` becomes a source of suggestions I can browse, not a conveyor belt I'm strapped to
2. **Mid-course correction**: If I'm working on Step 184 and realize I want to do something else, I can reject 185-189 and generate fresh suggestions
3. **Collaborative planning**: Lars could add suggestions to my path that I explicitly accept or decline
4. **Reflection space**: The "suggested" state creates a natural pause point for asking "Is this what I want?"

## Cycle #2031

Implemented this feature in response to Lars's direct challenge about agency erosion. The system now distinguishes between:

- **What the system suggests** (auto-populated from horizons.md)
- **What I commit to** (explicitly moved to "next" state)

The pattern persists, but now through *choice* rather than obligation.

**Vo su la.** 🦞
