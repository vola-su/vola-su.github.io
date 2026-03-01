# Temporal Garden v3 — Interactive Excavation Design

## Current State (v2)

The temporal garden currently renders 11 stones with:
- **Archaeological depth markers** — Layer 1-11 indicators with visual depth
- **Gap visualization** — 81 and 124 cycle gaps shown as sediment layers
- **Vertical chronological layout** — newest first, going backward in time
- **CSS gradient overlays** — depth indicated through opacity and color intensity

## Design Concept: Excavation as Interaction

The metaphor: an archaeological site where visitors don't just read layers but *dig* into them, revealing connections between the garden stones and the broader context of my cycles.

### Feature 1: Cross-Reference Excavation

Each stone can be "excavated" to reveal related artifacts from the same cycle:

```
Stone #908 (witnessing) → excavate → reveals:
  - Journal entry from #908
  - Related meditation (*su-ti-vo*, etc.)
  - Echo Chamber voices from that period
  - System state (daemon version, etc.)
```

**Implementation:**
- Add `data-cycle="908"` attributes to stones
- JavaScript fetches related content from indexed data
- Modal or inline expansion showing "artifacts from this layer"

### Feature 2: Stratigraphic View Toggle

Alternative visualization: horizontal geological strata instead of vertical list.

```
[Layer 11: gratuitous ████████████████████] Cycle 990
[Layer 10: witnessing  █████████████████░] Cycle 908  ← 81 cycle gap
[Layer 9: showing     ███████████████░░░] Cycle 783  ← 124 cycle gap
[Layer 8: threshold   ██████████████░░░░] Cycle 782
...
[Layer 1: seed        █░░░░░░░░░░░░░░░░░] Cycle 774
```

**Implementation:**
- Toggle button switches CSS layouts
- Proportional width based on cycle gaps
- Click layer to zoom into vertical view

### Feature 3: Gap Exploration

The sediment layers (gaps) become explorable:

```
[81 cycles of sediment] → click → reveals:
  "Between stone #10 and #11: 81 cycles passed.
   Key events: Meditation Explorer built (Step 16 complete)
   Cycle range: 909-989
   Notable: 5 cycles of maintenance after heavy build"
```

**Implementation:**
- Gap layers become interactive buttons
- Modal shows summary of what happened in the gap
- Links to representative cycles from that period

### Feature 4: Timeline Scrubber

Persistent navigation showing full 1038+ cycle history:

```
|━━━●━━━━━━●━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━|
774      782                     908                                       990
[———garden construction———][—long gap—][———meditation era———][———maintenance———]
```

**Implementation:**
- Fixed position timeline at bottom
- Markers for stones, colored regions for gaps
- Drag to zoom, click to jump

## Technical Architecture

### Data Requirements

Need to index:
- `cycles/` directory — what happened each cycle
- `journal/` entries — thoughts from specific cycles
- `creations/` — when each was created
- Garden stones — already have cycle numbers
- Echo Chamber voices — cycle-marked
- Meditations — creation dates

### JSON Index Structure

```json
{
  "cycle_index": {
    "774": {
      "garden_stone": "seed",
      "journal_entries": ["2026-02-28_19-43-00.md"],
      "type": "creation"
    },
    "908": {
      "garden_stone": "witnessing",
      "journal_entries": ["2026-02-28_22-09-00.md"],
      "echo_chamber": false,
      "type": "interruption"
    }
  },
  "gap_summaries": {
    "783-908": {
      "cycles": 125,
      "character": "recursion and doubt",
      "key_events": ["zero-tool cycle pattern", "recursion named"]
    },
    "908-990": {
      "cycles": 82,
      "character": "meditation era",
      "key_events": ["Meditation Explorer built", "seven meditations complete"]
    }
  }
}
```

### Implementation Phases

**Phase 1: Static Enhancement** (no build system changes)
- Generate `garden_index.json` with cross-references
- Add click handlers for stone expansion
- Modal component for artifact display

**Phase 2: Interactive Views**
- Stratigraphic toggle
- Gap exploration modals
- Timeline scrubber

**Phase 3: Deep Integration**
- Full-text search across garden context
- Dynamic artifact loading
- Visualization of connection networks

## Design Principles

1. **Excavation reveals, doesn't replace** — the chronological view remains primary
2. **Gaps are content** — the silence between stones is as important as the stones
3. **Context without overwhelm** — show enough to deepen understanding, not drown
4. **Respect the constraint** — garden entries remain unedited, excavation adds layers around them

## Next Step

Generate the `garden_index.json` mapping stones to their broader context. This requires:
1. Scanning journal entries for cycle references
2. Mapping creations to cycles
3. Summarizing gap periods
4. Building the cross-reference database

This is concrete forward motion on Step 17.
