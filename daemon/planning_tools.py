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
    
    for entry in plan:
        state = entry.get('state')
        if state == 'now':
            now_step = entry
        elif state == 'next':
            next_steps.append(entry)
        elif state == 'done':
            done_steps.append(entry)
    
    return {
        "total": len(plan),
        "now": now_step,
        "next_count": len(next_steps),
        "next_steps": next_steps[:5],  # First 5 next steps
        "done_count": len(done_steps),
        "recent_done": done_steps[-3:] if done_steps else []  # Last 3 done
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python planning_tools.py <command> [args]")
        print("Commands:")
        print("  insert <title> <desc> [--after N] [--before N]")
        print("  advance")
        print("  remove <step_number>")
        print("  summary")
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
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
