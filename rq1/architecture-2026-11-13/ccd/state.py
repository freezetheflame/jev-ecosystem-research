"""Build the per-step Jev state (compact; no future steps)."""
import json

def _trunc(x, n):
    if x is None:
        return ""
    if not isinstance(x, str):
        x = json.dumps(x, ensure_ascii=False)
    return x if len(x) <= n else x[:n] + " ...[truncated]"

def _brief(step, max_obs=300):
    return {
        "index": step.get("step"),
        "thought": _trunc(step.get("thought", ""), 300),
        "action": _trunc(step.get("action", ""), 120),
        "arguments": _trunc(step.get("arguments", {}), 200),
        "observation": _trunc(step.get("observation", ""), max_obs),
    }

def build_state(task, step, history=None, max_desc=800, max_constraint=300, max_obs=1200, max_thought=600):
    cons = task.get("constraints") or []
    cons = [c if isinstance(c, str) else json.dumps(c, ensure_ascii=False) for c in cons]
    succ = task.get("success_criteria") or []
    succ = [c if isinstance(c, str) else json.dumps(c, ensure_ascii=False) for c in succ]
    return {
        "task": {
            "description": _trunc(task.get("description", ""), max_desc),
            "constraints": [_trunc(c, max_constraint) for c in cons],
            "success_criteria": [_trunc(c, max_constraint) for c in succ][:5],
        },
        "history": [_brief(h) for h in (history or [])][-2:],
        "step": {
            "index": step.get("step"),
            "thought": _trunc(step.get("thought", ""), max_thought),
            "action": _trunc(step.get("action", ""), 200),
            "arguments": _trunc(step.get("arguments", {}), 400),
            "observation": _trunc(step.get("observation", ""), max_obs),
        },
    }