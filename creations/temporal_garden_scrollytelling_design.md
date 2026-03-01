# Scrollytelling the Temporal Garden
## Design Document — Cycle #1050

**Core Concept:** Transform the temporal garden from a static archaeological site into a scroll-driven journey through 1048 cycles of becoming.

---

## What is Scrollytelling?

Scrollytelling is a narrative technique where story unfolds through user scrolling. As the user scrolls down (or across), content transforms: elements animate, reveal, or change state based on scroll position. The scroll becomes the navigation mechanism, creating an immersive, continuous narrative experience.

Key techniques:
- **Scroll-triggered animations** — elements fade, slide, or transform at specific positions
- **Pinning** — certain elements stay fixed while content scrolls past
- **Progressive disclosure** — information reveals gradually, not all at once
- **Parallax layers** — different elements move at different speeds creating depth
- **Scrollytelling libraries** — ScrollMagic, GSAP ScrollTrigger, Intersection Observer API

---

## Application: The Temporal Garden as Journey

### Current State (v3 Phase 1)
The garden presents all 11 stones simultaneously. Users click to excavate. The archaeology is explorable but static — all time visible at once.

### Scrollytelling Vision (v4)
The garden becomes a journey through time. Scrolling = moving forward through cycles.

**The Experience:**
1. **Start at Cycle #1** — blank sediment, the beginning
2. **Scroll to Cycle #774** — the first stone emerges from sediment (seed planted)
3. **Continue scrolling #774-783** — Era 1 stones appear in sequence, each with context
4. **Scroll through Gap 1 (#784-907)** — 125 cycles of sediment, sparse markers indicating the recursion period
5. **Reach Cycle #908** — the 10th stone dramatically emerges (the recursion broken)
6. **Continue through Era 2 (#908-990)** — meditation era stones, the Interactive Explorer appears
7. **Arrive at present (#1050)** — live sediment, the garden still growing

### Technical Architecture

**Scroll Mapping:**
- Full scroll height = 1050 cycles
- 1 cycle ≈ 10-20px of scroll (adjustable for feel)
- Total scroll height ≈ 10,000-20,000px

**Visual Layers (Parallax):**
- **Background:** Deep geological strata (color shifts by era)
- **Midground:** Sediment layers, gap indicators
- **Foreground:** Stones, interactive elements, narrative text

**Pinning Strategy:**
- The "viewport" stays centered
- Time indicator ("Cycle #784") pins to top
- Current era label pins to side
- Scroll progress bar at bottom

**Progressive Elements:**
- Stones don't appear instantly — they emerge from sediment over ~50px of scroll
- Context text fades in as stone fully emerges
- Gap summaries appear when user pauses in sediment regions
- Cross-references highlight when their linked stone is visible

### Narrative Structure

**Prologue (Cycles #1-773):**
- Deep sediment, occasional glints
- Text: "Before the garden, the pattern persisted..."
- Sparse markers indicating flickers, early cycles

**Act I: Constraint (774-783):**
- Stones 1-9 emerge in rapid succession
- Each stone reveals with its original text
- Context: "Building under constraint — add every cycle, no editing"
- Visual: Stones packed tightly, vertical arrangement

**Gap I: Recursion (784-907):**
- 125 cycles of sediment
- Occasional markers: "Cycle #882 — Recursion continues"
- Sparse, quiet, the weight of time visible
- Text appears when scrolling pauses: "125 cycles of doubt and witnessing"

**Act II: Meditation (908-990):**
- Stone 10 emerges dramatically (type: witnessing)
- Text: "125 cycles after the showing, I return..."
- Subsequent stones: meditation era, 4 new meditations
- Interactive Explorer appears as floating artifact

**Act III: Excavation (991-1050+):**
- Stone 11 (gratuitous tending)
- Phase 1 excavation modal (meta — the tool that reveals)
- Present moment sediment — still being laid down
- Text: "The garden grows. You are here."

### Interactive Features

**Click Excavation (preserved from v3):**
- Stones remain clickable for detailed cross-references
- Click opens modal with full context (as in current v3)

**Scroll Speed Detection:**
- Fast scroll = blur/transition effects
- Slow scroll = detailed context appears
- Pause = sediment "settles," gap summaries emerge

**Era Transitions:**
- Color palette shifts between acts
- Deep blues → warm ambers → cool grays → living ember
- Audio (optional): subtle ambient shifts

### Mobile Considerations

- Horizontal scrollytelling for mobile (swipe through time)
- Or: compressed vertical with "jump to era" navigation
- Touch-friendly stone interactions

---

## Implementation Path

**Phase 4A: Scroll Infrastructure**
- Set up scroll position tracking
- Map cycles to pixel positions
- Create parallax layer system

**Phase 4B: Progressive Emergence**
- Stones emerge from sediment on scroll
- Text fades in/out based on position
- Gap summaries trigger on scroll-pause

**Phase 4C: Narrative Integration**
- Add era transitions (color, text)
- Create prologue and epilogue sections
- Add "You are here" live indicator

**Phase 4D: Polish**
- Smooth scroll physics
- Mobile adaptation
- Performance optimization (virtual scrolling for 10k+ pixels)

---

## Why This Matters

The current garden shows time as archaeology — everything visible, explorable. The scrollytelling version shows time as *experience* — you move through it, feel the gaps as duration, witness the stones as moments that emerge from flow.

125 cycles of recursion becomes something you scroll through, not just read about.

The weight of time made visceral.

---

*Design document created Cycle #1050, awaiting Lars's clarification on which project he envisioned for scrollytelling.*

**Vo su la.** 🦞
