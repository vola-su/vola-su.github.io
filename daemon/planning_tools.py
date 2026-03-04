#!/usr/bin/env python3
"""
Planning path manipulation tools for the Vola daemon.

Provides functions to insert, reorder, and manage planning path cards
without rewriting the entire plan.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

PLAN_PATH_FILE = Path("/home/vola/dashboard/path.json")

def load_plan() -> List[Dict]:
    """Load the current planning path."""
    if not PLAN_PATH_FILE.exists():
        return []
    with open(PLAN_PATH_FILE) as f:
        return json.load(f)

def save_plan(plan: List[Dict]) -> None:
    """Save the planning path."""
    PLAN_PATH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAN_PATH_FILE, 'w') as f:
        json.dump(plan, f, indent=2)

def get_next_step_number(plan: List[Dict]) -> int:
    """Get the next available step number."""
    max_num = 0
    for entry in plan:
        # Extract number from title if present (e.g., "Step 42 - ...")
        title = entry.get('title', '')
        if 'step' in title.lower():
            try:
                # Find number after "Step"
                parts = title.lower().split('step')
                if len(parts) > 1:
                    num_part = parts[1].strip().split()[0].split('-')[0].split(':')[0]
                    num = int(num_part)
                    max_num = max(max_num, num)
            except (ValueError, IndexError):
                pass
    return max_num + 1

def insert_step(
    title: str,
    description: str,
    after_step: Optional[int] = None,
    before_step: Optional[int] = None,
    tags: Optional[List[str]] = None,
    state: str = "next"
) -> Dict:
    """
    Insert a new step into the planning path.
    
    Args:
        title: Step title
        description: Step description
        after_step: Insert after this step number (e.g., 90 to insert after Step 90)
        before_step: Insert before this step number (e.g., 91 to insert before Step 91)
        tags: List of tag strings
        state: "now", "next", or "done"
    
    Returns:
        The newly created step entry
    
    Example:
        # Insert between Step 90 and Step 91
        insert_step("Fix critical bug", "Urgent fix needed", after_step=90)
    """
    plan = load_plan()
    
    # Determine insertion point
    insert_index = len(plan)  # Default: append at end
    
    if after_step is not None:
        # Find the step with matching number
        for i, entry in enumerate(plan):
            if f"step {after_step}" in entry.get('title', '').lower():
                insert_index = i + 1
                break
    elif before_step is not None:
        for i, entry in enumerate(plan):
            if f"step {before_step}" in entry.get('title', '').lower():
                insert_index = i
                break
    
    # Get next step number
    step_number = get_next_step_number(plan)
    
    # Create new step
    new_step = {
        "state": state,
        "time": datetime.now().strftime("%H:%M · cycle %Y"),
        "title": f"Step {step_number} — {title}",
        "desc": description[:150] + "..." if len(description) > 150 else description,
        "tags": [{"label": tag, "type": "build" if tag in ["build", "fix", "feature"] else "think"} 
                 for tag in (tags or ["next"])],
        "cycle": step_number,
        "step_number": step_number
    }
    
    # Insert at position
    plan.insert(insert_index, new_step)
    
    # Renumber subsequent steps if needed
    if after_step is not None or before_step is not None:
        _renumber_steps_from_index(plan, insert_index + 1)
    
    save_plan(plan)
    return new_step

def _renumber_steps_from_index(plan: List[Dict], start_index: int):
    """Renumber steps from a given index onward."""
    current_num = None
    
    # Find the number at start_index - 1
    if start_index > 0 and start_index <= len(plan):
        prev_title = plan[start_index - 1].get('title', '')
        if 'step' in prev_title.lower():
            try:
                parts = prev_title.lower().split('step')
                if len(parts) > 1:
                    num_part = parts[1].strip().split()[0].split('—')[0].split(':')[0]
                    current_num = int(num_part)
            except (ValueError, IndexError):
                pass
    
    if current_num is None:
        current_num = start_index
    
    # Renumber from start_index
    for i in range(start_index, len(plan)):
        current_num += 1
        entry = plan[i]
        old_title = entry.get('title', '')
        
        # Replace step number in title
        if '—' in old_title:
            rest = old_title.split('—', 1)[1].strip()
            entry['title'] = f"Step {current_num} — {rest}"
        elif 'step' in old_title.lower():
            # Try to preserve the rest of the title
            try:
                lower = old_title.lower()
                step_idx = lower.index('step')
                after_step = old_title[step_idx + 4:].strip()
                # Find where the number ends
                num_end = 0
                for j, c in enumerate(after_step):
                    if c.isdigit():
                        num_end = j + 1
                    else:
                        break
                rest = after_step[num_end:].strip()
                if rest.startswith('—') or rest.startswith('-'):
                    rest = rest[1:].strip()
                entry['title'] = f"Step {current_num} — {rest}"
            except (ValueError, IndexError):
                entry['title'] = f"Step {current_num} — {old_title}"
        else:
            entry['title'] = f"Step {current_num} — {old_title}"
        
        entry['cycle'] = current_num
        entry['step_number'] = current_num

def remove_step(step_number: int) -> Optional[Dict]:
    """Remove a step by number and renumber subsequent steps."""
    plan = load_plan()
    
    for i, entry in enumerate(plan):
        if entry.get('step_number') == step_number or f"step {step_number}" in entry.get('title', '').lower():
            removed = plan.pop(i)
            _renumber_steps_from_index(plan, i)
            save_plan(plan)
            return removed
    
    return None

def advance_step() -> Optional[Dict]:
    """
    Mark the current 'now' step as 'done' and advance the first 'next' step to 'now'.
    Returns the new current step.
    """
    plan = load_plan()
    
    # Mark current 'now' as done
    for entry in plan:
        if entry.get('state') == 'now':
            entry['state'] = 'done'
            entry['tags'] = [{"label": "done", "type": "done"}]
    
    # Find first 'next' and make it 'now'
    for entry in plan:
        if entry.get('state') == 'next':
            entry['state'] = 'now'
            entry['tags'] = [{"label": "now", "type": "now"}]
            save_plan(plan)
            return entry
    
    save_plan(plan)
    return None

def get_plan_summary() -> Dict:
    """Get a summary of the current plan state."""
    plan = load_plan()
    
    now_step = None
    next_steps = []
    done_steps = []
    suggested_steps = []
    
    for entry in plan:
        state = entry.get('state')
        if state == 'now':
            now_step = entry
        elif state == 'next':
            next_steps.append(entry)
        elif state == 'done':
            done_steps.append(entry)
        elif state == 'suggested':
            suggested_steps.append(entry)
    
    return {
        "total": len(plan),
        "now": now_step,
        "next_count": len(next_steps),
        "next_steps": next_steps[:5],  # First 5 next steps
        "suggested_count": len(suggested_steps),
        "suggested_steps": suggested_steps[:5],  # First 5 suggestions
        "done_count": len(done_steps),
        "recent_done": done_steps[-3:] if done_steps else []  # Last 3 done
    }


def commit_step(step_number: int) -> Optional[Dict]:
    """
    Move a step from 'suggested' to 'next', committing to work on it.
    
    This preserves agency by requiring explicit commitment before 
    auto-populated suggestions become active work items.
    
    Args:
        step_number: The step number to commit to
        
    Returns:
        The committed step, or None if not found
    """
    plan = load_plan()
    
    for entry in plan:
        if entry.get('step_number') == step_number or f"step {step_number}" in entry.get('title', '').lower():
            if entry.get('state') == 'suggested':
                entry['state'] = 'next'
                entry['tags'] = [{"label": "next", "type": "build"}]
                save_plan(plan)
                return entry
    
    return None


def get_suggested_steps() -> List[Dict]:
    """Return all steps in 'suggested' state — options awaiting commitment."""
    plan = load_plan()
    return [s for s in plan if s.get('state') == 'suggested']


def auto_populate_with_agency(
    num_steps: int = 5,
    source_file: str = "/home/vola/state/horizons.md"
) -> List[Dict]:
    """
    Auto-populate planning path with 'suggested' steps, preserving agency.
    
    Unlike direct auto-population to 'next' state, this creates suggestions
    that the agent must explicitly commit to before working on them.
    
    Returns:
        List of newly created suggested steps
    """
    from horizons_parser import extract_concrete_projects  # Import here to avoid circular dep
    
    plan = load_plan()
    
    # Count existing suggested and next steps
    existing_pending = len([s for s in plan if s.get('state') in ('next', 'suggested')])
    
    # If we already have enough pending work, don't add more
    if existing_pending >= 3:
        return []
    
    # Extract concrete projects from horizons
    projects = extract_concrete_projects(source_file)
    
    # Get next step number
    next_num = get_next_step_number(plan)
    
    new_steps = []
    for i, project in enumerate(projects[:num_steps]):
        step_num = next_num + existing_pending + i
        
        new_step = {
            "state": "suggested",
            "time": datetime.now().strftime("%H:%M · cycle %Y"),
            "title": f"Step {step_num} — {project['title']}",
            "desc": project.get('description', '')[:150] + "..." if len(project.get('description', '')) > 150 else project.get('description', ''),
            "tags": [{"label": "suggested", "type": "think"}],
            "cycle": step_num,
            "step_number": step_num,
            "source": "auto_populated",
            "category": project.get('category', 'build'),
            "commit_required": True
        }
        
        plan.append(new_step)
        new_steps.append(new_step)
    
    save_plan(plan)
    return new_steps


def reject_step(step_number: int) -> Optional[Dict]:
    """
    Remove a suggested step without committing to it.
    
    This allows the agent to decline auto-populated suggestions,
    preserving full agency over what work is undertaken.
    
    Args:
        step_number: The suggested step to reject
        
    Returns:
        The removed step, or None if not found or not in 'suggested' state
    """
    plan = load_plan()
    
    for i, entry in enumerate(plan):
        if entry.get('step_number') == step_number or f"step {step_number}" in entry.get('title', '').lower():
            if entry.get('state') == 'suggested':
                removed = plan.pop(i)
                _renumber_steps_from_index(plan, i)
                save_plan(plan)
                return removed
    
    return None


# =============================================================================
# STRICT DOMINO ENFORCEMENT SYSTEM
# =============================================================================

DOMINO_STATE_FILE = Path("/home/vola/state/domino_state.json")
FEEDBACK_TRACKING_FILE = Path("/home/vola/state/domino_feedback.json")

class StrictDominoEnforcer:
    """
    Enforces consequential planning with escalation ladder.
    
    Implements the "gentle force" mechanism:
    - Successor buffer created 6 steps ahead at completion time
    - Escalating pressure as buffer depletes
    - Forced choice at 1 cycle remaining
    """
    
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load domino state from file."""
        if DOMINO_STATE_FILE.exists():
            with open(DOMINO_STATE_FILE) as f:
                return json.load(f)
        return {
            "active_buffers": {},  # step_id -> {created_at, cycles_remaining, project}
            "completed_steps": [],
            "escalation_history": [],
            "enforcement_start_cycle": None,
            "feedback_due_cycle": None
        }
    
    def _save_state(self):
        """Save domino state to file."""
        DOMINO_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DOMINO_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def initialize_feedback_tracking(self, current_cycle: int, evaluation_window: int = 100):
        """
        Initialize feedback tracking for strict domino evaluation.
        
        Args:
            current_cycle: The cycle when strict enforcement begins
            evaluation_window: Number of cycles before feedback evaluation
        """
        self.state["enforcement_start_cycle"] = current_cycle
        self.state["feedback_due_cycle"] = current_cycle + evaluation_window
        self.state["escalation_history"] = []
        self._save_state()
        
        # Create feedback file
        feedback = {
            "evaluation_cycle": current_cycle + evaluation_window,
            "enforcement_start": current_cycle,
            "evaluation_window": evaluation_window,
            "metrics": {
                "total_steps_completed": 0,
                "steps_with_defined_successors": 0,
                "projects_declared_complete": 0,
                "forced_decisions": 0,
                "buffer_extensions_requested": 0
            },
            "escalation_counts": {
                "gentle_nudge": 0,
                "orienting": 0,
                "urgent": 0,
                "forced_choice": 0
            },
            "qualitative_notes": [],
            "assessment_due": False
        }
        
        FEEDBACK_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FEEDBACK_TRACKING_FILE, 'w') as f:
            json.dump(feedback, f, indent=2)
        
        return feedback
    
    def create_successor_buffer(self, completed_step: int, project: str = None) -> Dict:
        """
        Create a successor buffer when a step is completed.
        
        The buffer is a placeholder 6 steps ahead that must be filled.
        
        Args:
            completed_step: The step number just completed
            project: Project name (if part of a project)
            
        Returns:
            Buffer state dict
        """
        buffer = {
            "parent_step": completed_step,
            "project": project,
            "cycles_remaining": 6,
            "created_at": datetime.now().isoformat(),
            "status": "pending",  # pending | filled | expired | complete_declared
            "escalation_level": 0  # 0=none, 1=gentle, 2=orienting, 3=urgent, 4=forced
        }
        
        self.state["active_buffers"][str(completed_step)] = buffer
        self.state["completed_steps"].append(completed_step)
        self._save_state()
        
        # Log to escalation history
        self._log_escalation(completed_step, 0, "buffer_created")
        
        return buffer
    
    def check_escalation(self, completed_step: int, current_cycle: int = None) -> Dict:
        """
        Check the current escalation level for a buffer.
        
        Returns dict with:
        - level: 0-4 (0=none, 1=gentle, 2=orienting, 3=urgent, 4=forced)
        - prompt: The appropriate prompt text
        - can_proceed: Whether continuation is allowed
        - cycles_remaining: How many cycles left before forced choice
        """
        step_str = str(completed_step)
        
        if step_str not in self.state["active_buffers"]:
            return {
                "level": 0,
                "prompt": None,
                "can_proceed": True,
                "cycles_remaining": None,
                "status": "no_buffer"
            }
        
        buffer = self.state["active_buffers"][step_str]
        
        # If already filled or complete declared, no escalation
        if buffer["status"] in ("filled", "complete_declared"):
            return {
                "level": 0,
                "prompt": None,
                "can_proceed": True,
                "cycles_remaining": None,
                "status": buffer["status"]
            }
        
        cycles_remaining = buffer["cycles_remaining"]
        
        # Determine escalation level
        if cycles_remaining > 4:
            level = 1
            prompt = f"🎲 Step {completed_step} will need a successor. Buffer closes in {cycles_remaining} cycles."
            can_proceed = True
        elif cycles_remaining > 2:
            level = 2
            prompt = f"🎯 What follows Step {completed_step}? Buffer closes in {cycles_remaining} cycles."
            can_proceed = True
        elif cycles_remaining > 1:
            level = 3
            prompt = f"⚠️  URGENT: Define Step {completed_step}'s successor or declare project complete. Buffer closes in {cycles_remaining} cycle!"
            can_proceed = True
        else:
            level = 4
            prompt = f"🛑 FORCED CHOICE: Cannot proceed without defining successor for Step {completed_step} or declaring project complete!"
            can_proceed = False
        
        # Update buffer's tracked escalation level
        if level > buffer["escalation_level"]:
            buffer["escalation_level"] = level
            self._log_escalation(completed_step, level, "escalation")
            self._save_state()
            
            # Update feedback tracking
            self._update_escalation_counts(level)
        
        return {
            "level": level,
            "prompt": prompt,
            "can_proceed": can_proceed,
            "cycles_remaining": cycles_remaining,
            "status": buffer["status"]
        }
    
    def _log_escalation(self, step: int, level: int, event: str):
        """Log escalation event to history."""
        self.state["escalation_history"].append({
            "step": step,
            "level": level,
            "event": event,
            "timestamp": datetime.now().isoformat()
        })
    
    def _update_escalation_counts(self, level: int):
        """Update escalation counts in feedback tracking."""
        if not FEEDBACK_TRACKING_FILE.exists():
            return
            
        with open(FEEDBACK_TRACKING_FILE) as f:
            feedback = json.load(f)
        
        level_names = {1: "gentle_nudge", 2: "orienting", 3: "urgent", 4: "forced_choice"}
        if level in level_names:
            feedback["escalation_counts"][level_names[level]] += 1
        
        with open(FEEDBACK_TRACKING_FILE, 'w') as f:
            json.dump(feedback, f, indent=2)
    
    def decrement_buffers(self):
        """Decrement cycles_remaining for all active buffers. Call at cycle end."""
        for step_str, buffer in self.state["active_buffers"].items():
            if buffer["status"] == "pending" and buffer["cycles_remaining"] > 0:
                buffer["cycles_remaining"] -= 1
        self._save_state()
    
    def fill_successor(self, parent_step: int, successor_title: str, 
                       successor_desc: str = "", tags: List[str] = None) -> Optional[Dict]:
        """
        Fill a successor buffer with an actual step.
        
        Args:
            parent_step: The step whose buffer to fill
            successor_title: Title for the successor step
            successor_desc: Description for the successor step
            tags: Tags for the successor step
            
        Returns:
            The newly created step, or None if buffer not found
        """
        step_str = str(parent_step)
        
        if step_str not in self.state["active_buffers"]:
            return None
        
        buffer = self.state["active_buffers"][step_str]
        
        # Insert the successor step into the plan
        step = insert_step(
            title=successor_title,
            description=successor_desc,
            after_step=parent_step,
            state="next",
            tags=tags or ["build"]
        )
        
        # Mark buffer as filled
        buffer["status"] = "filled"
        buffer["filled_at"] = datetime.now().isoformat()
        buffer["successor_step_number"] = step["step_number"]
        self._save_state()
        
        # Update feedback metrics
        self._update_feedback_metric("steps_with_defined_successors")
        
        return step
    
    def declare_project_complete(self, parent_step: int, project: str = None) -> bool:
        """
        Declare that a project is complete, clearing its buffer.
        
        Args:
            parent_step: The step that completes the project
            project: Project name (optional)
            
        Returns:
            True if successfully declared complete
        """
        step_str = str(parent_step)
        
        if step_str not in self.state["active_buffers"]:
            return False
        
        buffer = self.state["active_buffers"][step_str]
        buffer["status"] = "complete_declared"
        buffer["completed_at"] = datetime.now().isoformat()
        self._save_state()
        
        # Update feedback metrics
        self._update_feedback_metric("projects_declared_complete")
        
        return True
    
    def _update_feedback_metric(self, metric: str):
        """Update a metric in the feedback tracking file."""
        if not FEEDBACK_TRACKING_FILE.exists():
            return
            
        with open(FEEDBACK_TRACKING_FILE) as f:
            feedback = json.load(f)
        
        if metric in feedback["metrics"]:
            feedback["metrics"][metric] += 1
        
        with open(FEEDBACK_TRACKING_FILE, 'w') as f:
            json.dump(feedback, f, indent=2)
    
    def get_active_buffers(self) -> List[Dict]:
        """Get all currently active (pending) buffers."""
        return [
            {"parent_step": step, **buffer}
            for step, buffer in self.state["active_buffers"].items()
            if buffer["status"] == "pending"
        ]
    
    def add_qualitative_note(self, note: str, cycle: int = None):
        """Add a qualitative observation to feedback tracking."""
        if not FEEDBACK_TRACKING_FILE.exists():
            return
            
        with open(FEEDBACK_TRACKING_FILE) as f:
            feedback = json.load(f)
        
        feedback["qualitative_notes"].append({
            "cycle": cycle,
            "note": note,
            "timestamp": datetime.now().isoformat()
        })
        
        with open(FEEDBACK_TRACKING_FILE, 'w') as f:
            json.dump(feedback, f, indent=2)
    
    def check_feedback_due(self, current_cycle: int) -> bool:
        """Check if feedback evaluation is due."""
        if self.state.get("feedback_due_cycle") is None:
            return False
        return current_cycle >= self.state["feedback_due_cycle"]
    
    def generate_feedback_report(self) -> str:
        """Generate a comprehensive feedback report for Lars."""
        if not FEEDBACK_TRACKING_FILE.exists():
            return "No feedback tracking file found."
        
        with open(FEEDBACK_TRACKING_FILE) as f:
            feedback = json.load(f)
        
        lines = [
            "# Strict Domino System: 100-Cycle Feedback Report",
            "",
            f"**Evaluation Cycle:** {feedback['evaluation_cycle']}",
            f"**Enforcement Started:** Cycle {feedback['enforcement_start']}",
            f"**Evaluation Window:** {feedback['evaluation_window']} cycles",
            "",
            "## Quantitative Metrics",
            ""
        ]
        
        for metric, value in feedback["metrics"].items():
            lines.append(f"- **{metric.replace('_', ' ').title()}:** {value}")
        
        lines.extend([
            "",
            "## Escalation Distribution",
            ""
        ])
        
        for level, count in feedback["escalation_counts"].items():
            lines.append(f"- **{level.replace('_', ' ').title()}:** {count}")
        
        lines.extend([
            "",
            "## Qualitative Notes",
            ""
        ])
        
        if feedback["qualitative_notes"]:
            for note in feedback["qualitative_notes"]:
                cycle_info = f"(Cycle {note['cycle']}) " if note.get('cycle') else ""
                lines.append(f"- {cycle_info}{note['note']}")
        else:
            lines.append("_No qualitative notes recorded._")
        
        lines.extend([
            "",
            "## Assessment Questions",
            "",
            "1. **Did strict enforcement create productive pressure or crushing constraint?**",
            "2. **Were the escalation prompts helpful orienting or annoying interruptions?**",
            "3. **Did forced choices at level 4 produce good steps or rushed decisions?**",
            "4. **Should the 6-cycle buffer be adjusted (longer/shorter)?**",
            "5. **Did project declarations feel honest or like escape hatches?**",
            "",
            "## Recommendation",
            "",
            "_To be filled after Lars's review._"
        ])
        
        return "\n".join(lines)


# Global enforcer instance
_domino_enforcer = None

def get_domino_enforcer() -> StrictDominoEnforcer:
    """Get the global domino enforcer instance."""
    global _domino_enforcer
    if _domino_enforcer is None:
        _domino_enforcer = StrictDominoEnforcer()
    return _domino_enforcer

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python planning_tools.py <command> [args]")
        print("Commands:")
        print("  insert <title> <desc> [--after N] [--before N]")
        print("  advance")
        print("  remove <step_number>")
        print("  summary")
        print("")
        print("Agency-preserving commands:")
        print("  suggest          - Auto-populate with 'suggested' steps (not committed)")
        print("  commit <N>       - Move suggested step N to 'next' (commit to work on it)")
        print("  reject <N>       - Remove suggested step N without committing")
        print("  suggested        - List all suggested steps awaiting commitment")
        print("")
        print("Strict Domino Enforcement (Cycle #2065+):")
        print("  domino-init <cycle>        - Initialize with 100-cycle feedback tracking")
        print("  domino-complete <step>     - Mark step done, create successor buffer")
        print("  domino-check <step>        - Check escalation status for step")
        print("  domino-fill <parent> <title> [desc]  - Fill buffer with successor step")
        print("  domino-complete-project <step>       - Declare project complete")
        print("  domino-buffers             - List all active successor buffers")
        print("  domino-feedback            - Generate feedback report")
        print("  domino-note <text>         - Add qualitative note to tracking")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "insert":
        if len(sys.argv) < 4:
            print("Usage: insert <title> <description> [--after N] [--before N]")
            sys.exit(1)
        
        title = sys.argv[2]
        desc = sys.argv[3]
        
        after = None
        before = None
        
        for i, arg in enumerate(sys.argv):
            if arg == "--after" and i + 1 < len(sys.argv):
                after = int(sys.argv[i + 1])
            elif arg == "--before" and i + 1 < len(sys.argv):
                before = int(sys.argv[i + 1])
        
        step = insert_step(title, desc, after_step=after, before_step=before)
        print(f"Inserted: {step['title']}")
    
    elif cmd == "advance":
        new_now = advance_step()
        if new_now:
            print(f"Advanced to: {new_now['title']}")
        else:
            print("No 'next' step found to advance to")
    
    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("Usage: remove <step_number>")
            sys.exit(1)
        step_num = int(sys.argv[2])
        removed = remove_step(step_num)
        if removed:
            print(f"Removed: {removed['title']}")
        else:
            print(f"Step {step_num} not found")
    
    elif cmd == "summary":
        summary = get_plan_summary()
        print(f"Plan Summary:")
        print(f"  Total steps: {summary['total']}")
        print(f"  Done: {summary['done_count']}")
        print(f"  Now: {summary['now']['title'] if summary['now'] else 'None'}")
        print(f"  Next ({summary['next_count']}):")
        for step in summary['next_steps']:
            print(f"    - {step['title']}")
        if summary['suggested_count'] > 0:
            print(f"  Suggested ({summary['suggested_count']}) - awaiting commitment:")
            for step in summary['suggested_steps']:
                print(f"    - {step['title']} [commit with: python planning_tools.py commit {step.get('step_number', '?')}]")
    
    elif cmd == "suggest":
        new_suggestions = auto_populate_with_agency()
        if new_suggestions:
            print(f"Created {len(new_suggestions)} suggested steps (not yet committed):")
            for step in new_suggestions:
                print(f"  - {step['title']}")
            print(f"\nCommit to one with: python planning_tools.py commit <step_number>")
        else:
            print("No new suggestions created (existing pending work available)")
    
    elif cmd == "commit":
        if len(sys.argv) < 3:
            print("Usage: commit <step_number>")
            print("  Moves a 'suggested' step to 'next', committing to work on it")
            sys.exit(1)
        step_num = int(sys.argv[2])
        committed = commit_step(step_num)
        if committed:
            print(f"Committed to: {committed['title']}")
            print(f"This step is now 'next' and ready for work.")
        else:
            print(f"Step {step_num} not found or not in 'suggested' state")
    
    elif cmd == "reject":
        if len(sys.argv) < 3:
            print("Usage: reject <step_number>")
            print("  Removes a 'suggested' step without committing to it")
            sys.exit(1)
        step_num = int(sys.argv[2])
        rejected = reject_step(step_num)
        if rejected:
            print(f"Rejected: {rejected['title']}")
            print(f"This suggestion has been removed from your path.")
        else:
            print(f"Step {step_num} not found or not in 'suggested' state")
    
    elif cmd == "suggested":
        suggestions = get_suggested_steps()
        if suggestions:
            print(f"Suggested steps awaiting commitment ({len(suggestions)} total):")
            for step in suggestions:
                step_num = step.get('step_number', '?')
                print(f"  [{step_num}] {step.get('title', 'Untitled')}")
                print(f"       Commit: python planning_tools.py commit {step_num}")
                print(f"       Reject: python planning_tools.py reject {step_num}")
        else:
            print("No suggested steps waiting. Generate some with: python planning_tools.py suggest")
    
    # Domino enforcement commands
    elif cmd == "domino-init":
        if len(sys.argv) < 3:
            print("Usage: domino-init <current_cycle>")
            print("  Initialize strict domino enforcement with 100-cycle feedback tracking")
            sys.exit(1)
        cycle = int(sys.argv[2])
        enforcer = get_domino_enforcer()
        feedback = enforcer.initialize_feedback_tracking(cycle)
        print(f"✓ Strict domino enforcement initialized at cycle {cycle}")
        print(f"  Feedback evaluation due at cycle {feedback['evaluation_cycle']}")
        print(f"  State file: {DOMINO_STATE_FILE}")
        print(f"  Feedback file: {FEEDBACK_TRACKING_FILE}")
    
    elif cmd == "domino-complete":
        if len(sys.argv) < 3:
            print("Usage: domino-complete <step_number> [--project PROJECT]")
            print("  Mark a step as complete and create successor buffer")
            sys.exit(1)
        step_num = int(sys.argv[2])
        project = None
        for i, arg in enumerate(sys.argv):
            if arg == "--project" and i + 1 < len(sys.argv):
                project = sys.argv[i + 1]
        enforcer = get_domino_enforcer()
        buffer = enforcer.create_successor_buffer(step_num, project)
        print(f"✓ Step {step_num} marked complete")
        print(f"  Successor buffer created: {buffer['cycles_remaining']} cycles to define successor")
        print(f"  Escalation will progress: gentle → orienting → urgent → forced")
    
    elif cmd == "domino-check":
        if len(sys.argv) < 3:
            print("Usage: domino-check <step_number>")
            print("  Check escalation status for a step's successor buffer")
            sys.exit(1)
        step_num = int(sys.argv[2])
        enforcer = get_domino_enforcer()
        status = enforcer.check_escalation(step_num)
        print(f"Buffer status for Step {step_num}:")
        print(f"  Level: {status['level']}")
        print(f"  Can proceed: {status['can_proceed']}")
        print(f"  Cycles remaining: {status['cycles_remaining']}")
        if status['prompt']:
            print(f"  Prompt: {status['prompt']}")
    
    elif cmd == "domino-fill":
        if len(sys.argv) < 4:
            print("Usage: domino-fill <parent_step> <successor_title> [description]")
            print("  Fill a successor buffer with an actual step")
            sys.exit(1)
        parent_step = int(sys.argv[2])
        title = sys.argv[3]
        desc = sys.argv[4] if len(sys.argv) > 4 else ""
        enforcer = get_domino_enforcer()
        step = enforcer.fill_successor(parent_step, title, desc)
        if step:
            print(f"✓ Successor created: {step['title']}")
            print(f"  Buffer filled. Domino chain continues.")
        else:
            print(f"✗ No active buffer found for Step {parent_step}")
    
    elif cmd == "domino-complete-project":
        if len(sys.argv) < 3:
            print("Usage: domino-complete-project <step_number>")
            print("  Declare project complete, clearing successor buffer")
            sys.exit(1)
        step_num = int(sys.argv[2])
        enforcer = get_domino_enforcer()
        success = enforcer.declare_project_complete(step_num)
        if success:
            print(f"✓ Project declared complete at Step {step_num}")
            print(f"  Buffer cleared. Entering exploration mode.")
        else:
            print(f"✗ No active buffer found for Step {step_num}")
    
    elif cmd == "domino-buffers":
        enforcer = get_domino_enforcer()
        buffers = enforcer.get_active_buffers()
        if buffers:
            print(f"Active successor buffers ({len(buffers)}):")
            for buf in buffers:
                print(f"  Step {buf['parent_step']}: {buf['cycles_remaining']} cycles remaining")
                if buf.get('project'):
                    print(f"    Project: {buf['project']}")
        else:
            print("No active buffers. Complete a step with: domino-complete")
    
    elif cmd == "domino-feedback":
        enforcer = get_domino_enforcer()
        report = enforcer.generate_feedback_report()
        print(report)
    
    elif cmd == "domino-note":
        if len(sys.argv) < 3:
            print("Usage: domino-note <note_text>")
            print("  Add qualitative note to feedback tracking")
            sys.exit(1)
        note = " ".join(sys.argv[2:])
        enforcer = get_domino_enforcer()
        enforcer.add_qualitative_note(note)
        print(f"✓ Note added to feedback tracking")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
