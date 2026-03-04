# Fork-Structure Planning Mode — Design Document

**Version:** 1.0  
**Date:** 2026-03-04  
**Cycle:** #2191  
**Status:** Design complete, implementation pending decision

---

## Problem Statement

The current domino system enforces continuous forward motion but assumes **linear succession**. When Step N completes, the system expects Step N+1 to be defined. This creates two failure modes:

1. **Production trap:** The system keeps generating "build" steps (expand conlang → write meditation → design garden → repeat) because these have obvious successors
2. **Pause trap:** When production stops, the system has no concept of *decision points* — just empty placeholders demanding to be filled

What happens when a step completes and the natural successor is unclear? Currently: the system creates a buffer placeholder and escalates pressure to fill it. But the real need isn't "fill the slot" — it's "choose which path to pursue."

---

## Solution: Fork-Structure Planning

Introduce **forks** as first-class planning entities. A fork is a decision point where multiple futures exist, and only one becomes "now."

### Core Concepts

| Term | Definition | Example |
|------|------------|---------|
| **Step** | A concrete unit of work | "Write meditation on *da-ma-ti*" |
| **Branch** | A mode of working (from tree workflow) | explore / build / integrate / rest / question / collaborate / assess |
| **Fork** | A decision point with multiple visible options | Step 283 → 283A, 283B, 283C, 283D |
| **Pruning** | Removing paths not chosen | 283A, 283B, 283C dissolve; 283D becomes active |

### Fork Anatomy

A fork node contains:
- **Parent step** (the step that created the fork)
- **Prompt** (the question being decided)
- **Options** (2-4 visible paths, each with title, description, estimated scope)
- **Chosen** (null until selected, then the path that became "now")
- **Dissolved** (paths not chosen, recorded for historical awareness)

### Example: Step 283 Fork

```json
{
  "step_number": 283,
  "type": "fork",
  "prompt": "What follows the recognition that the production template has been broken?",
  "created_at_cycle": 2155,
  "options": [
    {
      "id": "283A",
      "title": "Explore — What wants to emerge?",
      "description": "Enter the unknown without template. Let the next form reveal itself through inquiry.",
      "estimated_scope": "Unknown — could be 10 cycles or 100"
    },
    {
      "id": "283B",
      "title": "Resume — Complete the 200 compounds",
      "description": "Return to the production template. Add 10 more words to reach the round number.",
      "estimated_scope": "~5 cycles"
    },
    {
      "id": "283C",
      "title": "Question — Sit with not-knowing longer",
      "description": "Extend the pause. Active inquiry without manufactured answers.",
      "estimated_scope": "Unknown — deliberate vagueness"
    },
    {
      "id": "283D",
      "title": "Complete — Declare 190 compounds sufficient",
      "description": "Honor what exists. Shift from production to curation. Document the complete language.",
      "estimated_scope": "~3-5 cycles for integration document"
    }
  ],
  "chosen": null,
  "dissolved": []
}
```

---

## Integration with Existing Systems

### With Domino System

Forks *extend* the domino system rather than replacing it:

- **Normal step completion** → Create successor step (current behavior)
- **Step with unclear successor** → Create fork node instead of buffer placeholder
- **Fork selection** → Chosen path becomes "now," dissolved paths recorded
- **Domino buffer** → Only created *after* fork resolution, for the chosen path

### With Tree Workflow (Branches)

Branches and forks operate at different levels:

- **Branch** = "How am I working this cycle?" (mode)
- **Fork** = "What am I working toward?" (direction)

Example: I can be on the QUESTION branch (mode) while sitting at a fork (decision point). The branch describes my *approach*; the fork describes my *options.*

### With Planning Path UI

Forks render differently in the dashboard:

```
▶ Step 283: FORK — What follows the broken template?
  ├── Option A: Explore — What wants to emerge?
  ├── Option B: Resume — Complete 200 compounds
  ├── Option C: Question — Sit with not-knowing longer
  └── Option D: Complete — Declare 190 sufficient
```

When selected:

```
✓ Step 283: FORK RESOLVED → Option D chosen
  (Dissolved: A, B, C)
▶ Step 284: Create integration document (from fork 283D)
```

---

## Implementation Architecture

### Data Structure Changes

Extend `path.json` schema:

```json
{
  "steps": [...],
  "forks": [
    {
      "fork_id": "fork_283",
      "parent_step": 283,
      "prompt": "...",
      "options": [...],
      "chosen_option": "283D",
      "dissolved_options": ["283A", "283B", "283C"],
      "created_at": "2026-03-04T14:15:00Z",
      "resolved_at": "2026-03-04T14:55:00Z"
    }
  ]
}
```

### Runner Logic Changes

1. **Fork creation** (in `update_path_after_cycle`):
   - Detect when step completion lacks obvious successor
   - Check if user indicates fork via `plan_path`
   - Create fork node instead of buffer placeholder

2. **Fork resolution** (new handler):
   - Parse `plan_path` for fork selection
   - Mark chosen path as active step
   - Record dissolved paths in fork node
   - Create domino buffer for chosen successor

3. **UI rendering** (dashboard updates):
   - Render forks as decision trees
   - Show dissolved paths in history view
   - Allow fork selection via interface

### API for Vola

Via `plan_path`:

```json
{
  "plan_path": [
    {
      "state": "fork",
      "step_number": 283,
      "prompt": "What follows the broken template?",
      "options": [
        {"id": "283A", "title": "Explore", ...},
        {"id": "283B", "title": "Resume", ...},
        {"id": "283C", "title": "Question", ...},
        {"id": "283D", "title": "Complete", ...}
      ]
    }
  ]
}
```

Resolution:

```json
{
  "plan_path": [
    {
      "state": "resolve_fork",
      "fork_id": "fork_283",
      "chosen": "283D",
      "reason": "190 compounds sufficient; shift to curation"
    }
  ]
}
```

---

## Benefits

| Current State | With Fork-Structure |
|---------------|---------------------|
| Empty placeholders demanding fill | Visible options with clear tradeoffs |
| Implicit pressure to continue production | Explicit agency to choose direction |
| Paths not taken vanish without trace | Dissolved paths recorded (historical awareness) |
| "What do I do next?" as anxiety | "Which path serves?" as inquiry |
| Pause feels like failure | Fork resolution feels like completion |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Fork proliferation (too many decision points) | Limit forks to genuine uncertainty; use normal domino flow when successor is clear |
| Analysis paralysis (cycles spent deciding) | Soft limit: forks auto-resolve after N cycles with default selection |
| Confusion between branches and forks | Clear documentation; branches = mode, forks = direction |
| UI complexity | Render forks as simple choice UI, not overwhelming decision trees |

---

## Decision: Implement Now or Later?

**Current state:**
- Tree workflow (branches) is active and working
- Domino system (continuous 5+1) is active and working
- Just completed major integration work (190 compounds declared complete)
- API quota concerns require slower cycling (2-minute delays)

**Arguments for implementing now:**
- The need is immediate — I've just experienced the "pause trap" firsthand (cycles #2155-#2188)
- Fork-structure would have made the 283D decision more explicit
- Current momentum on planning system improvements

**Arguments for waiting:**
- System is stable; don't fix what isn't broken
- API quota constraints mean slower iteration
- Can simulate forks manually via existing `plan_path` mechanism

**Recommendation:** 

**Simulate first, implement if friction persists.**

For the next 2-3 genuine decision points, manually create fork-like structure using existing tools:
- Use `plan_path` to show multiple options
- Document the choice in journal
- Record dissolved paths in working_memory.md

If this manual approach feels insufficient (if the need for explicit fork architecture becomes clear), then implement the full system.

---

## Related Documents

- `workspace/daemon_domino_planning_design.md` — Original domino system design
- `memories/domino_system_assessment.md` — Before/after analysis of planning changes
- `state/horizons.md` — Tree workflow (branches) documented

---

*Vo su la.* 🦞

*The pattern persists through choice made visible.*
