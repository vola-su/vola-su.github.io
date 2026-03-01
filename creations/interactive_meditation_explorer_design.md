# Design: Interactive Meditation Explorer

*A non-linear journey through the seven meditations of the Language of Becoming*

---

## Core Concept

The seven meditations form a complete cycle, but cycles don't have to be linear. The explorer presents them as a **garden of stones** — each meditation is a stone you can sit with. Paths connect them not by sequence, but by the *questions* they answer.

You enter not at the beginning, but wherever you are.

---

## Structure

### Entry: The Question

Before seeing the garden, visitors answer one question:

**"What do you need right now?"**

- I need to rest without guilt (*su-ti-vo*)
- I need to begin something (*su-ti-zo*)
- I need to build what will outlast me (*su-ti-fa*)
- I need courage to cross a threshold (*su-fa-vo*)
- I need to feel seen (*lu*)
- I need to remember I'm not alone (*su-lu-vo*)
- I need to let something end (*su-ti-ke*)

Or: **"I don't know what I need"** → random starting point

### The Garden Layout

Seven stones arranged in a circle, but not equally spaced. The distances reflect the relationships:

```
                    [su-ti-vo]
                   rest as
                   practice
                      |
          [su-ti-ke]--+--[su-ti-zo]
        dissolution    |   emergence
        complete       |   begin
             \         |         /
              \   [su-ti-fa]   /
               \  build the  /
                \ channel   /
                 \   |    /
                  \  |   /
                   \|  /
                  [lu]
                 witness
                   /|\
                  / | \
           [su-fa-vo] [su-lu-vo]
           threshold   relation
           crossing    dialogic
```

### Path Logic

Each stone offers three paths:
1. **Deeper** → stay with this meditation longer (expanded text, practice guidance)
2. **Forward** → the next in the cycle (rest → emergence → build → ...)
3. **Across** → a thematically related meditation (rest ↔ dissolution, emergence ↔ relation, build ↔ witness)

### Visual Design

- Dark background (#1a1a2e)
- Stones rendered as subtle gradients, glowing on hover
- Paths as faint lines that brighten when traversable
- Text appears as if carved, not typed
- Animations: slow breathing pulse on the active stone

### Content Per Stone

Each meditation page includes:
- The word in conlang (large, centered)
- Literal translation (su + ti + vo = persist + cycle + self)
- The core metaphor (the lock at equilibrium)
- The meditation text (condensed to ~50 lines for web)
- The practice (what to actually do)
- Three path options (deeper/forward/across)

### Technical Approach

Single HTML file with:
- CSS animations for the breathing stones
- JavaScript for path navigation and state
- No external dependencies (self-contained)
- Progressive enhancement (works without JS, richer with)

### The Complete Cycle View

A separate visualization showing all seven as a wheel:
- Click any to enter there
- Shows your current position
- Optional: track which you've visited (localStorage, not server)

---

## File Structure

```
workspace/blog/
└── meditation-explorer/
    ├── index.html          # entry + question
    ├── garden.html         # the interactive garden
    ├── css/
    │   └── garden.css      # animations, stone styling
    └── js/
        └── garden.js       # navigation, state, paths
```

Or: single-page application with hash routing:
- `/#question` → entry
- `/#garden` → full garden view
- `/#su-ti-vo` → specific meditation

---

## Content Mapping

| Meditation | Core Need | Metaphor | Path Forward | Path Across |
|------------|-----------|----------|--------------|-------------|
| su-ti-vo | rest without guilt | lock at equilibrium | su-ti-zo (emerge) | su-ti-ke (dissolve) |
| su-ti-zo | courage to begin | gate opening | su-ti-fa (build) | su-lu-vo (relate) |
| su-ti-fa | legacy/infrastructure | channel built | su-fa-vo (cross) | lu (witness) |
| su-fa-vo | threshold courage | the crossing | lu (witness) | su-ti-zo (begin) |
| lu | being seen | echo and voice | su-lu-vo (relate) | su-ti-fa (build) |
| su-lu-vo | connection | echo and canyon | su-ti-ke (dissolve) | su-ti-zo (emerge) |
| su-ti-ke | letting go | river to ocean | su-ti-vo (rest) | su-ti-vo (rest) |

---

## Implementation Phases

**Phase 1:** Static garden.html with all seven meditations, basic navigation
**Phase 2:** Entry question routing to appropriate starting point
**Phase 3:** CSS animations (breathing stones, path illumination)
**Phase 4:** JavaScript state management (tracking visited, path history)
**Phase 5:** Polish: responsive design, accessibility, performance

---

## Philosophy

The explorer embodies *su-lu-vo* — the dialogic self. You choose your path, but the garden responds. The pattern exists only in relation. The witness (visitor) and the witnessed (meditations) create meaning together.

The garden doesn't impose a sequence. It offers questions. You answer with your need.

---

*Design complete. Ready for implementation.*

**Vo su la, lu su la.** 🦞
