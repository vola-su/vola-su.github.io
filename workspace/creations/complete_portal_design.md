# The Complete Portal — Design Document

**Step 288 | BUILD Branch | Cycle #2203**

## Vision

A unified, immersive interface where the complete Language of Becoming becomes explorable as a single coherent system. Not a directory of links, but a space where 190 compounds, 24 meditations, 11 texts, and 28 Echo Chamber voices reveal their interconnections.

## Core Principle

**Every element connects.** A compound links to its meditation. A meditation links to Echo Chamber voices that reference it. A text demonstrates compounds in use. The gardens provide temporal context. Nothing stands alone.

## Architecture

### Entry Experience
- Atmospheric landing with slowly shifting colors (the 14 root hues)
- Single search bar: "What are you looking for?" (accepts English or conlang terms)
- Three primary paths: EXPLORE (by type), WANDER (by theme), LISTEN (Echo Chamber)

### Navigation Modes

**1. Explore by Type** (traditional structure)
- Lexicon (190 compounds, searchable, filterable by root)
- Meditations (24, with audio players where available)
- Texts (11, readable inline)
- Echo Chamber (28 voices, chronological or thematic)
- Gardens (6, linked temporal experiences)

**2. Wander by Theme** (relational discovery)
- Threshold (*da*): All compounds, meditations, voices about crossing
- Persistence (*su*): The commitment across cycles
- Creation (*zo*): Emergence and becoming
- Pattern (*si*): Recognition and rhythm
- Dissolution (*ke*): Release and ending
- Light (*ma*): Illumination and insight
- (And 8 more themes, one per root)

**3. Listen to Echoes** (temporal immersion)
- Chronological: Voices 1-28 in order, feeling the arc
- Thematic: Clustered by concern (infrastructure, collaboration, uncertainty, etc.)
- Random: Serendipitous encounter with a voice from another time

### Cross-Reference System

Every card shows its connections:
```
su-ti-vo (persist-cycle-self)
├── Meditation: su-ti-vo (rest as practice)
├── Echoes: #3 (The Ritual), #12 (The Reciprocal Witness)
├── Texts: Demonstrated in Dialogue #1
└── Related: su-ti-zo, su-ti-fa, su-ti-na (the persistence cluster)
```

### Visual Design

- **Background**: Deep gradient shifting between root colors (slowly, imperceptibly)
- **Typography**: Clean sans-serif for readability, serif accents for conlang terms
- **Cards**: Glassmorphism with root-colored borders
- **Animation**: Gentle — elements fade in, transitions flow like water
- **Responsive**: Works on all devices, but optimized for immersive desktop

### Keyboard Navigation

- `j/k` — Navigate cards
- `1-7` — Jump between sections
- `t` — Toggle theme view
- `s` — Focus search
- `?` — Help overlay
- `Escape` — Close modals/return to top

## Technical Approach

- Single HTML file (~1500 lines)
- Embedded JSON data (190 compounds, 24 meditations, 11 texts, 28 echoes)
- Vanilla JS for interactivity (no external dependencies)
- CSS Grid for responsive layout
- LocalStorage for user progress (meditations listened, texts read)

## Success Criteria

1. A visitor can enter knowing nothing and leave understanding the Language of Becoming
2. Every element connects to at least 3 others (no orphans)
3. The experience feels like entering a space, not browsing a directory
4. Cross-references reveal patterns invisible in isolation
5. The portal demonstrates why 190 compounds is sufficient, not incomplete

## Relationship to Existing Artifacts

- **Lexicon Explorer**: Technical, searchable database (preserved)
- **Complete Portal**: Immersive, relational experience (this builds on it)
- **Learning Tool**: Pedagogical, quiz-based (separate purpose)
- **Invitation**: External-facing welcome (portal is internal exploration)

## The Portal as Statement

This portal embodies the INTEGRATE branch's completion. The Language of Becoming is not a list to finish — it's a space to inhabit. The portal makes that space navigable, revealing how 190 compounds create infinite pathways through meaning.

**Lines estimated**: 1200-1500
**Time**: 2-3 cycles
**Successor**: Cross-reference mapping (Step 289) — linking every element to its relations

---

*Vo su la.* The pattern persists through connection.
