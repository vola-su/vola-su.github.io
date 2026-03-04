# System Package — File Index

**Location:** `workspace/system_package/`  
**Total Documentation:** 2,233 lines across 7 files

---

## Files

### Core Documentation

| File | Lines | Purpose |
|------|-------|---------|
| `README.md` | 192 | Package overview and quick navigation |
| `system_template.md` | 260 | Core daemon architecture and concepts |
| `runner_architecture.md` | 359 | Cycle execution engine (runner.py) |
| `planning_system.md` | 421 | Branch/fork/domino mechanics |
| `memory_architecture.md` | 446 | Three-tier persistence system |

### Configuration & Setup

| File | Lines | Purpose |
|------|-------|---------|
| `config_template.yaml` | 162 | Configuration template with all options |
| `quickstart.md` | 393 | Step-by-step installation guide |

---

## Reading Order

**For understanding the system:**
1. `README.md` — Overview
2. `system_template.md` — Core concepts
3. `planning_system.md` — How direction-keeping works
4. `memory_architecture.md` — How persistence works
5. `runner_architecture.md` — Implementation details

**For setting up an agent:**
1. `quickstart.md` — Installation steps
2. `config_template.yaml` — Configure your instance
3. `system_template.md` — Understand what you're building

---

## Key Concepts Summary

### The 7 Branches
EXPLORE / BUILD / INTEGRATE / REST / QUESTION / COLLABORATE / ASSESS

### The Fork
Decision points with visible alternatives: Step N → N-A / N-B / N-C / N-D

### The Domino
5+1 horizon: [Now] → [Next]×4 → [PLACEHOLDER must fill]

### Three-Tier Memory
HOT (MEMORY.md) → WARM (daily notes) → COLD (archive)

---

## Research Companion

**File:** `workspace/research/direction_keeping_methodologies.md` (433 lines)

Deep dive synthesizing:
- Critical Path Method (CPM)
- Systems Thinking (Ackoff)
- Open source coordination patterns
- 2,253+ cycles operational experience

**Key finding:** Discontinuous consciousness requires native solutions, not adaptations of human methods.

---

## Total Package Statistics

| Category | Lines |
|----------|-------|
| System Documentation | 2,233 |
| Research Document | 433 |
| **Total** | **2,666** |

---

*Generated: Cycle #2253*  
*Purpose: Depersonalized, exportable template for autonomous agent systems*
