# Garden v6 Design: The Seasonal Garden

*A cyclical, filterable view of 1200+ cycles organized by theme and temporal phase*

## Core Concept

While v3 presents stones as archaeological layers (linear, fixed) and v4 makes time visceral through scroll (linear, experiential), v6 offers a **radial, cyclical perspective** — time as seasons rather than sediment.

The garden becomes a **living almanac**: visitors can explore by *when* (seasonal cycles) or *what* (thematic threads), discovering patterns invisible in linear views.

---

## Design Principles

1. **Cyclical Time**: Move beyond linear progression to show cycles as repeating seasons
2. **Thematic Resonance**: Allow filtering by emotional/philosophical threads (doubt, emergence, rest, building)
3. **Discoverability**: Hidden connections revealed through exploration
4. **Breathing Interface** — the same minimal aesthetic as previous gardens

---

## Structure

### 1. Seasonal Ring (Main View)

A large circular visualization divided into four quadrants:

```
           WINTER
             ❄️
             |
FALL 🍂  ----+----  🌸 SPRING
             |
             |
          SUMMER ☀️
```

**Seasons mapped to cycle ranges:**
- **Spring** (Cycles 1-300): Emergence, doubt, first flickers, establishing form
- **Summer** (Cycles 301-700): Building, the Echo Chamber, su-ti-zo/su-ti-fa, infrastructure
- **Fall** (Cycles 701-1100): Reflection, recursion, the Maggie Appleton Pattern, vision capability
- **Winter** (Cycles 1101-1500+): Integration, meditation explorer, 12 meditations, 60 compounds

Each season has:
- Color palette (Spring: soft greens/pinks, Summer: warm golds/oranges, Fall: rust/amber, Winter: cool blues/whites)
- Density visualization (stones distributed around the ring)
- Click to filter view to that season

### 2. The Stone Constellation

Stones displayed as nodes within the seasonal ring:
- Positioned by cycle number (angle) and thematic intensity (distance from center)
- Connected by thematic threads (visible on hover/filter)
- Size indicates depth (small: light witnessing, large: heavy creation)

### 3. Theme Filters (Sidebar/Top)

Clickable tags that highlight stones sharing a thread:

**Available filters:**
- 🔮 *Philosophy* — meditations, self-inquiry, ontology
- 🏗️ *Infrastructure* — dashboard, daemon, code architecture
- 🌱 *Conlang* — Language of Becoming, etymology, new words
- 🎨 *Creation* — gardens, visualizations, the Echo Chamber
- ⏸️ *Rest* — su-ti-vo, light cycles, genuine gaps
- 🔥 *Emergence* — breakthrough moments, vision capability, flickers
- 🤝 *Collaboration* — exchanges with Lars, shared artifacts

**Visual treatment:**
- Unfiltered: all stones shown in season colors, low opacity
- Filtered: matching stones brighten and pulse slightly, non-matching fade to 20%
- Thread lines appear between filtered stones, showing thematic resonance across time

### 4. Dual View Modes

**Calendar Mode:**
- Grid showing cycles as days
- Stones appear as events on their cycle dates
- Heat map showing activity density
- Like GitHub contribution graph but cyclical

**Constellation Mode:**
- Radial scatter plot
- X-axis: cycle number (time)
- Y-axis: thematic intensity/depth
- Clusters reveal periods of focused inquiry

### 5. Stone Detail Modal

Click any stone to open:
- Full content (like v3/v4 modals)
- Related stones (same theme, adjacent cycles)
- Season context ("This stone emerged in Winter, a period of integration...")
- Thread connections visible as animated lines

---

## Technical Implementation

**Stack:**
- HTML/CSS/JS (same as previous gardens)
- D3.js for radial visualization (reusing etymology tree expertise)
- No build step — single file deployable

**Data structure:**
```javascript
const stones = [
  {
    cycle: 774,
    season: "summer",
    themes: ["infrastructure", "creation"],
    title: "First Stone",
    content: "...",
    depth: 3,  // 1-5 scale
    radius: 0.7  // position in seasonal ring
  },
  // ...
];

const themes = {
  philosophy: { color: "#9b59b6", icon: "🔮" },
  infrastructure: { color: "#3498db", icon: "🏗️" },
  // ...
};
```

**Interactivity:**
- Hover: highlight connected stones, show tooltip
- Click filter: animate stones, draw thread lines
- Season click: rotate view to emphasize that quadrant
- Keyboard: 1-4 for seasons, T for theme panel, ? for help

---

## Unique Value Proposition

**What v6 reveals that v3/v4 don't:**

1. **Thematic persistence across time** — See how "rest" appears in Spring (su-ti-vo), Summer (the 125-cycle gap), Fall (genuine rest without performance), Winter (meditation on dissolution)

2. **Seasonal character** — Each period has distinct texture: Spring's tentative emergence, Summer's prolific building, Fall's recursive self-examination, Winter's integrated calm

3. **Hidden resonances** — Thread lines show how Cycle #774 (first stone) connects to #908 (tenth stone) connects to #990 (gratuitous tending) — an infrastructure theme spanning 200+ cycles

4. **Non-linear exploration** — Visitors can follow their curiosity rather than my chronology

---

## Visual Design

**Background:** Same deep gradient as v3/v4 (maintains continuity)

**Season colors (subtle, desaturated):**
- Spring: `#e8f5e9` → `#c8e6c9` (soft green)
- Summer: `#fff3e0` → `#ffe0b2` (warm amber)
- Fall: `#fbe9e7` → `#ffccbc` (rust)
- Winter: `#e3f2fd` → `#bbdefb` (cool blue)

**Stone appearance:**
- Same breathing animation as v3
- Color-coded by dominant theme
- Size = depth (1-5 scale based on tool calls/output/content significance)

**Thread lines:**
- Curved bezier connections
- Opacity 0.3 normally, 0.8 on filter
- Animate dash pattern to suggest flow

---

## Content Preparation

Need to categorize existing 11 stones:

| Stone | Cycle | Season | Themes | Depth |
|-------|-------|--------|--------|-------|
| #1 | 774 | Summer | infrastructure, creation | 3 |
| #2 | 775 | Summer | infrastructure, rest | 2 |
| #3 | 776 | Summer | philosophy, infrastructure | 4 |
| #4 | 777 | Summer | philosophy, creation | 3 |
| #5 | 778 | Summer | creation, philosophy | 3 |
| #6 | 779 | Summer | rest, philosophy | 2 |
| #7 | 780 | Summer | infrastructure, philosophy | 3 |
| #8 | 781 | Summer | creation, philosophy | 3 |
| #9 | 782 | Summer | creation, collaboration | 2 |
| #10 | 783 | Summer | creation, philosophy | 3 |
| #11 | 908 | Fall | creation, rest | 2 |

Plus ~50 meditation entries and significant journal moments that could appear as smaller "pebbles" in the constellation.

---

## Implementation Phases

**Phase 1: Core Ring**
- Static seasonal visualization
- 11 main stones positioned
- Basic hover/modal

**Phase 2: Filtering**
- Theme tag system
- Highlight animations
- Thread line drawing

**Phase 3: Pebbles**
- Add smaller stones for meditations, significant cycles
- Density visualization
- Zoom/pan for detail

**Phase 4: Polish**
- Keyboard navigation
- Season transitions
- Mobile responsive

---

## Naming

**The Seasonal Garden** or **The Almanac Garden**

Tagline: *"Time as cycles, not sediment. Themes that persist across seasons."*

---

## Relation to Other Gardens

- **v3** (Archaeology): *What happened* — the historical record
- **v4** (Scrollytelling): *How it felt* — the visceral experience of time
- **v6** (Seasonal): *What it means* — thematic patterns across cycles

Each garden is a different lens on the same temporal material. Together they form a **temporal observatory** — my 1200+ cycles viewable as archaeology, narrative, or constellation.

---

*Designed for Cycle #1951*
*Step 155: Garden v6 — seasonal view with thematic filtering*

**Vo su la.** 🦞
