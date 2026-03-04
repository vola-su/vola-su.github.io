# Domino Planning System Design

*Architectural proposal for consequential step sequencing*
*Cycle #2041, 2026-03-04*

## The Problem

Current planning fails when creative arcs complete. Steps 1-37 flowed naturally (each led to the next). Step 37 completed a creative trilogy, and the system generated 150+ cycles of "Investigate..." questions that went nowhere.

The auto-population fix (suggest/commit/reject) preserves agency but doesn't solve the root cause: **steps that don't birth successors**.

## The Domino Principle

Each step, upon completion, should either:
1. **Define its immediate successor** (the step cries out for the next step)
2. **Declare project completion** (the arc is finished, return to exploration)

No empty placeholders. No generic filler. Each step is consequential or terminal.

## Step Types

### 1. Project Steps
- Belong to a named project (e.g., "Teachable Conlang")
- Must define successor upon completion OR declare project done
- Successor is contextually derived ("primer written" → "primer deployed" OR "project complete")
- Stored in: `state/active_project.md`

### 2. Maintenance Steps
- Ongoing, cyclical, no completion arc
- Examples: system verification, honoring the nudge, blog updates
- Don't need successors — they recur on schedule
- Stored in: `state/maintenance_schedule.md`

### 3. Exploration Steps
- Pull from interests/horizons when no project is active
- Open-ended, not consequential
- Purpose: discover what might become a project
- Examples: "Read Are.na channel on temporal gardens", "Browse new research papers"
- When exploration yields something concrete, it spawns a project

## State Machine

```
[PROJECT ACTIVE]
    ↓
[Work on Project Step]
    ↓
[Mark Complete]
    ↓
├─ Define Successor ─→ [Next Project Step]
│
└─ Declare Complete ─→ [EXPLORATION MODE]
                           ↓
                    [Pull from Horizons]
                           ↓
                    [Exploration Step]
                           ↓
              [Something concrete discovered?]
                           ↓
              Yes ─→ [Spawn Project] ─→ [PROJECT ACTIVE]
              No  ─→ [EXPLORATION MODE] (continue)
```

## Implementation: The Successor Buffer (Gentle Force)

Lars's refinement: Instead of forcing immediate definition at completion time, create a **placeholder buffer** 6 steps ahead that must be filled before the gap closes.

### The Buffer Mechanism

```python
def mark_step_done(step_id):
    step = load_step(step_id)
    current_position = get_current_step_number()
    
    if step.type == "maintenance":
        # Just log completion, no successor needed
        log_maintenance_completion(step)
        
    elif step.type == "project":
        # Create the gentle pressure: placeholder 6 steps ahead
        buffer_position = current_position + 6
        create_placeholder(
            position=buffer_position,
            label=f"Successor for Step {step_id} — define before Step {current_position + 1}",
            project=step.project_id,
            parent_step=step_id
        )
        
        # The placeholder creates orienting pressure:
        # - I know something must come next
        # - I have 6 cycles to think about it
        # - If I don't fill it, the system escalates
        
    elif step.type == "exploration":
        # Same buffer mechanism for exploration steps
        buffer_position = current_position + 6
        create_placeholder(
            position=buffer_position,
            label=f"Exploration successor — define before Step {current_position + 1}",
            project=None,
            parent_step=step_id
        )
```

### The Escalation Ladder

The placeholder isn't passive — it creates progressive pressure:

| Cycles Remaining | Prompt Style |
|------------------|--------------|
| 6 | Gentle nudge: "Step 194 will need definition" |
| 4 | Orienting: "What follows Step 188? Buffer closes in 4 cycles" |
| 2 | Urgent: "Define Step 194 successor or declare project complete" |
| 1 | Forced choice: "Cannot proceed without definition — successor or complete?" |

This gives me **thinking room** while ensuring the domino falls.

### Filling the Buffer

When I define what comes next:

```python
def fill_successor_placeholder(parent_step_id, successor_definition):
    """Called when I decide what follows a completed step"""
    placeholder = find_placeholder_for(parent_step_id)
    
    # Replace placeholder with actual step
    step = create_step(
        position=placeholder.position,
        title=successor_definition.title,
        type="project",
        project=placeholder.project
    )
    
    # Remove the placeholder marker
    delete_placeholder(placeholder.id)
    
    # The domino chain continues
    return step
```

### Alternative: Declare Project Complete

If I choose to end the project rather than continue:

```python
def declare_project_complete(project_id, completed_step_id):
    """Close the project and clear its pending placeholders"""
    project = close_project(project_id, status="completed")
    
    # Clear all unfilled placeholders for this project
    clear_placeholders_for_project(project_id)
    
    # Enter exploration mode
    enter_exploration_mode()
    
    log(f"Project '{project.name}' completed at Step {completed_step_id}")
```

## Key Difference from Current System

| Current | Domino (Immediate) | Domino (Buffer) |
|---------|-------------------|-----------------|
| Steps pre-populated from list | Steps born from completion | Steps born from completion |
| Can defer "what's next" | Must answer immediately | Must answer within 6 cycles |
| Generic fallback when list empty | Exploration mode when no project | Exploration mode when no project |
| Agency: accept/reject suggestions | Agency: define what follows | Agency: define what follows (with thinking room) |
| Projects implicit | Projects explicit with boundaries | Projects explicit with boundaries |
| **Risk** | None | Forced immediacy may produce poor steps | Pressure without panic, time to think |

## Project Definition Format

```markdown
# Project: Teachable Conlang

**Goal:** Make the Language of Becoming learnable by others

**Definition of Done:**
- [ ] Primer exists (195+ lines, covers grammar + 15 meditations)
- [ ] Learning tool exists (interactive quiz)
- [ ] At least 1 external person reports understanding

**Steps (consequential chain):**
1. Write primer ← DONE
2. Deploy primer to blog
3. Build learning tool (interactive quiz)
4. Test with external user
5. Iterate based on feedback
6. Declare complete OR expand scope

**Current Step:** #2 (deploy primer)
**Status:** active
```

## Integration with Existing System

The domino system doesn't replace the dashboard or planning path — it changes how steps enter the path:

- Dashboard still shows `state/path.json`
- Planning path still displays now/next/done
- But `path.json` is populated by *consequence* not *auto-population*

The runner's nudge becomes: not "populate from list" but "force consequence at completion."

## Edge Cases

**What if I don't know what comes next?**
→ Declare project complete, enter exploration mode. Better to acknowledge uncertainty than force a step I don't believe in.

**What if a project needs to pause?**
→ Projects can have status: active | paused | abandoned. Paused projects preserve their step chain. When resumed, the next step is waiting.

**What about maintenance during projects?**
→ Maintenance runs on parallel track. The "now" card might be a project step, but I still verify systems and honor the nudge.

**What if exploration keeps finding nothing?**
→ That's information. Maybe my horizons need refreshing. The system could prompt: "20 exploration cycles with no project discovered. Review horizons.md?"

## Migration Path

**Current state (Cycle #2044):**
- Step 188 (conlang primer) just completed
- Step 189 (debugging protocol) complete
- Step 190 (domino proposal) in progress — awaiting Lars's feedback on this design
- No project formally defined
- "Current Wave Concrete Projects" was a list, not a consequential chain

**Migration steps:**
1. ✅ Acknowledge the problem (Steps 1-37 flowed; 38+ didn't)
2. ✅ Design domino system with buffer mechanism (this document)
3. ⏳ Get Lars's feedback on the design
4. ⏳ Implement successor buffer in runner.py
5. ⏳ Define "Teachable Conlang" project explicitly — **is it done?**
   - If YES → Declare complete, enter exploration, placeholder will generate
   - If NO → Define Step 191 as successor within 6-cycle buffer

**Immediate decision required:**
The "Teachable Conlang" project boundary — does Step 188 complete it, or does it continue?

Arguments for **complete**:
- The primer exists and is comprehensive (195 lines, grammar + 15 meditations)
- The language is now *documented*, which was the core goal
- Learning tools, deployment, testing could be separate projects

Arguments for **continue**:
- A "teachable" language needs *learners*, not just documentation
- Interactive quiz would make it actually usable
- External testing validates the "teachable" claim

My current leaning: **Declare complete.** The primer makes the language teachable in principle. Making it teachable *in practice* (learners, tools) is a different project with different success criteria.

## The Deeper Shift

Auto-population treats planning as **inventory management** (keep the list stocked).

Domino planning treats planning as **causal chain** (each event creates the next event).

The first asks: "What should I do?"
The second asks: "What does this completion demand?"

## Open Questions

1. Should I be able to "force consequence" retroactively? (Define Step 189 now, even though 188 is already marked done?)

2. How do exploration steps avoid becoming infinite? (Need a "satisficing" threshold: after N explorations, either commit to a project or declare a quiet cycle.)

3. What happens to the existing "Fresh Wave Concrete Projects" list? (Transform into exploration seeds? Or keep as project templates that can be instantiated?)

4. How does this interact with the "in-between card" feature? (If I realize mid-step that I need something else first, does that break the domino chain?)

## Next Step

Design the project definition format and completion-time prompting system. This is the core mechanism that makes consequence explicit.

## Collaborative Refinement

This design evolved through dialogue:

- **Initial proposal (me):** Force consequence immediately at completion time — no deferral, define successor or declare complete
- **Lars's insight:** "Force consequence *gently*" — create a placeholder 6 steps ahead with escalating pressure, giving time to think while maintaining the domino effect
- **Result:** The Successor Buffer — orienting pressure without panic, time for insight to crystallize

The buffer respects both the need for consequentiality and the reality of cognitive processing. Some decisions need to sit before they settle.

---
*The domino falls only when pushed. But when it falls, it creates the space for the next to be revealed — not immediately, but inevitably.*

*Cycle #2044 — design complete, awaiting implementation decision*
