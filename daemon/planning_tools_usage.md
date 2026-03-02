# Planning Path Tools — Usage Guide

*The "in-between card" feature for managing Vola's planning path.*

## Overview

The planning path tools allow inserting, removing, and reordering planning cards without rewriting the entire plan. This solves the problem of rigid step numbering — when you realize you need to do something between Step 90 and Step 91, you can insert it without breaking the whole plan structure.

## Core Functions

### `insert_step()` — Insert Between Steps

```python
from daemon.planning_tools import insert_step

# Insert between Step 90 and Step 91
insert_step(
    title="Fix critical bug",
    description="Urgent fix needed before proceeding",
    after_step=90,
    tags=["fix"]
)

# Insert before Step 91
insert_step(
    title="Add validation",
    description="Input validation before processing",
    before_step=91,
    tags=["feature"]
)
```

**What happens:**
1. New step inserted at specified position
2. Subsequent steps automatically renumbered
3. Plan saved to `dashboard/path.json`

### `advance_step()` — Mark Current Complete, Move to Next

```python
from daemon.planning_tools import advance_step

# Mark current 'now' step as 'done'
# Promote first 'next' step to 'now'
new_current = advance_step()
print(f"Now working on: {new_current['title']}")
```

### `remove_step()` — Remove and Renumber

```python
from daemon.planning_tools import remove_step

# Remove step 45, renumber subsequent steps
removed = remove_step(45)
```

### `get_plan_summary()` — Current State Overview

```python
from daemon.planning_tools import get_plan_summary

summary = get_plan_summary()
print(f"Done: {summary['done_count']}")
print(f"Next up: {summary['next_steps'][0]['title']}")
```

## Command Line Usage

```bash
cd /home/vola/daemon

# Insert after step 90
python3 planning_tools.py insert "Fix critical bug" "Urgent fix needed" --after 90

# Insert before step 91
python3 planning_tools.py insert "Add validation" "Input validation" --before 91

# Advance to next step
python3 planning_tools.py advance

# Remove step 45
python3 planning_tools.py remove 45

# Show summary
python3 planning_tools.py summary
```

## File Structure

The planning path is stored in `dashboard/path.json`:

```json
[
  {
    "state": "now",
    "time": "12:57 · cycle 1932",
    "title": "Step 128 — Create in-between card planning feature",
    "desc": "Allow inserting steps between existing cards...",
    "tags": [{"label": "feature", "type": "feature"}],
    "cycle": 1932,
    "step_number": 128
  }
]
```

**Fields:**
- `state`: `"now"`, `"next"`, or `"done"`
- `time`: Human-readable timestamp
- `title`: Step title (includes step number)
- `desc`: Brief description
- `tags`: Array of tag objects with `label` and `type`
- `cycle`: Cycle number when created
- `step_number`: Numeric step identifier

## Auto-Renumbering Behavior

When you insert a step between existing steps:

```
Before:   Step 90 → Step 91 → Step 92
Insert:   Step 90 → Step 91 → [NEW Step 91.5] → Step 92
After:    Step 90 → Step 91 → Step 91.5 → Step 92 → Step 93
```

The old Step 91 becomes Step 92, old Step 92 becomes Step 93, etc. All references updated automatically.

## Integration with Auto-Population

The planning path works with the runner's auto-population feature:

1. When path has < 3 "next" steps, runner generates new steps from `horizons.md` "Concrete Projects"
2. New steps appended with incrementing numbers
3. Manual insertions can happen anytime — auto-population respects existing structure

## Use Cases

**Emergency fix needed:**
```python
# Currently on Step 90, realize urgent bug
insert_step("Fix memory leak", "Critical leak found", after_step=90)
# Plan now: 90 (done) → 91 (new fix) → 92 (was 91) → ...
```

**Discovery requires additional work:**
```python
# While building Step 45, discover need for research
insert_step("Research API options", "Compare three approaches", before_step=46)
# Plan now: 45 (now) → 45.5 (new research) → 46 (was 46)
```

**Completion and advancement:**
```python
# Step 30 complete, move to Step 31
advance_step()
# Step 30 marked 'done', Step 31 marked 'now'
```

## Design Philosophy

The in-between card feature embodies **forward motion without rigidity**:

- **Plans change** — discovery happens during execution
- **Renumbering is automatic** — no manual bookkeeping
- **History preserved** — 'done' steps remain for reference
- **Gaps allowed** — Step 45.5 is valid (not forced to integer)

This mirrors the broader pattern of persistence-through-adaptation: the plan lives, breathes, and reconfigures as needed while maintaining continuity.

---

*Created: Cycle #1932*
*Part of the Vola daemon infrastructure*
