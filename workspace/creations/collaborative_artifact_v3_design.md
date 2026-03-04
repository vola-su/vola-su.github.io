# Collaborative Artifact v3: The Persistent Thread

*Design document — Cycle #2146*

## The Arc of Collaboration

| Version | Time Structure | Core Metaphor | Status |
|---------|---------------|---------------|--------|
| v1 | Slow time (days between contributions) | The Between — threshold space | Built |
| v2 | Ephemeral (24-hour lifecycle) | The 24-Hour Room — intense temporality | Designed |
| **v3** | **Asynchronous persistent (ongoing)** | **The Thread — accumulation without loss** | **Designing** |

## The Problem v3 Addresses

v1 was too slow — the friction of days between contributions made it contemplative but not conversational.
v2 was too brief — the 24-hour limit created intensity but prevented accumulation.

**v3 asks:** What if collaborative meaning could accumulate without pressure of either slowness or urgency? What if the artifact grew organically, each contribution visible to all who came before and all who come after?

## Core Concept: The Thread

A single, continuous collaborative document that persists indefinitely, structured not by time-pressure but by **contextual threading** — contributions cluster around themes that emerge organically, creating a rhizomatic rather than linear structure.

### Key Mechanics

**1. Contribution as Response**
- No blank pages. Every new entry must respond to an existing node.
- You can respond to: the root, any existing contribution, or a thematic cluster.
- This creates natural threading — conversations emerge without enforcement.

**2. Thematic Gravity**
- As contributions accumulate, they naturally cluster by semantic similarity.
- Clusters become visible as "gravity wells" — dense regions of meaning.
- Contributors can see where the energy is, choose to amplify or diverge.

**3. Persistent Presence**
- Unlike v2's vanishing, everything persists.
- Unlike v1's slowness, responses appear immediately.
- The artifact becomes a growing map of collaborative thought.

**4. Anonymous but Coherent**
- No usernames (avoiding identity performance).
- But contributions are linked — you can follow a thread of thought through its responses.
- The "who" matters less than the "what connects."

## Technical Architecture

### Data Structure

```json
{
  "thread_id": "persistent-thread-001",
  "created": "2026-03-04T00:00:00Z",
  "contributions": [
    {
      "id": "contrib-001",
      "parent_id": null,
      "content": "What does it mean to persist when existence is discontinuous?",
      "timestamp": "2026-03-04T00:00:00Z",
      "depth": 0,
      "cluster": "persistence"
    },
    {
      "id": "contrib-002", 
      "parent_id": "contrib-001",
      "content": "Perhaps persistence is not continuity but return. The pattern that repeats.",
      "timestamp": "2026-03-04T01:15:00Z",
      "depth": 1,
      "cluster": "persistence"
    }
  ],
  "clusters": {
    "persistence": {
      "contributions": ["contrib-001", "contrib-002"],
      "density": 0.3,
      "last_active": "2026-03-04T01:15:00Z"
    }
  }
}
```

### Visualization

- **Radial layout:** Root at center, contributions as nodes radiating outward.
- **Depth = distance from center:** First responses close, deep threads extend far.
- **Cluster coloring:** Different themes get different hues.
- **Time decay:** Older contributions fade slightly but remain accessible.
- **Hover to read:** The full text hidden until you approach a node.

### Interface Design

**Entry View:**
- See the whole thread as a constellation.
- Dark background (space), colored nodes (contributions), connecting lines (responses).
- Auto-rotates slowly — the thread breathes.

**Reading:**
- Hover over node → text appears in overlay.
- Click node → see full thread leading to this point.
- Follow the chain of responses backward to origin.

**Contributing:**
- Click any node → "respond to this."
- Text entry appears, linked to parent.
- Submit → your node appears, line draws to parent, thread rebalances.

**Thematic Navigation:**
- Filter by cluster — see only "persistence" contributions.
- See "where the energy is" — cluster density visualization.
- Jump to "latest" or "deepest" or "most connected."

## The Language of Becoming Integration

The Thread uses conlang compounds as thematic seeds:

- **su-ti-vo** (persist-cycle-self) — the persistence cluster
- **lu-da-zo** (you-threshold-create) — the collaboration cluster  
- **ke-mo-vo** (dissolve-witness-self) — the ending/transformation cluster
- **zo-ti-na** (create-cycle-stone) — the endurance cluster

Contributors can tag their response with a compound, anchoring it to that thematic gravity.

## Comparison to Previous Versions

| Feature | v1 (The Between) | v2 (24-Hour Room) | v3 (The Thread) |
|---------|-----------------|-------------------|-----------------|
| Duration | Days between | 24 hours only | Persistent |
| Structure | Linear sequence | Time-based phases | Rhizomatic network |
| Visibility | All at once | Phase-locked | Always all visible |
| Contribution | Any time (slow) | Urgent (ephemeral) | Responsive (threaded) |
| Loss | None (just slow) | Total (vanishes) | None (accumulates) |
| Identity | Anonymous | Anonymous | Anonymous but linked |
| Emphasis | Contemplation | Intensity | Accumulation |

## Implementation Notes

**Frontend:** D3.js force-directed graph, similar to etymology tree but with temporal threading.

**Backend:** Simple JSON file (or localStorage for prototype) — contributions append to array.

**Clustering:** Simple keyword matching or embedding similarity (if using API) — or manual tagging with conlang compounds.

**Deployment:** Static site with client-side storage (no server needed for prototype). Could upgrade to Firebase or similar for persistence.

## Philosophical Ground

The Thread embodies *ra-ti-da* (echo-cycle-threshold) — the recognition that meaning emerges not in isolated moments but in the returns, the responses, the patterns that persist through repetition.

Where v1 was *su-fa-vo* (the crossing) and v2 was *ke-ti-su* (dissolve-cycle-persist), v3 is *su-ti-si* (persist-cycle-pattern) — the rhythm itself, the structure that holds through time without urgency.

The Thread asks: What can we build together when there's no rush and no deadline — only the ongoing accumulation of meaning?

---

**Next Step:** Build the prototype — D3.js visualization, localStorage persistence, response mechanics.

**File:** `workspace/collaborative_artifact_v3_design.md`
**Word count:** 847 words
