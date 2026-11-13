"""CCD detector: per-step constraint probes (one Jev request per step, k noul questions)."""
import time
from .probes import build_questions
from .state import build_state

def parse_noul(payload):
    out = {}
    for k, v in (payload.get("answers") or {}).items():
        if isinstance(v, dict) and v.get("type") == "noul":
            out[k] = v.get("noul")
    return out

class CCDDetector:
    def __init__(self, client, threshold=0.5, max_calls=None, save_step_payloads=False):
        self.client = client
        self.threshold = threshold
        self.max_calls = max_calls
        self.save_step_payloads = save_step_payloads

    def run(self, case):
        task = case["view"]["task"]
        steps = case["view"]["steps"]
        questions, meta = build_questions(task)
        c0, t0, l0 = self.client.calls, self.client.in_tokens, self.client.seconds
        step_scores = []
        payloads = []
        partial = False
        detection_step = None
        history = []
        for st in steps:
            if self.max_calls is not None and self.client.calls >= self.max_calls:
                partial = True
                break
            state = build_state(task, st, history)
            res = self.client.ask(state, questions)
            probs = parse_noul(res["payload"])
            vals = [v for v in probs.values() if isinstance(v, (int, float))]
            score = max(vals) if vals else None
            step_scores.append(dict(step=st.get("step"), score=score, p=probs,
                                    latency=res["latency"], request_sha256=res["request_sha256"]))
            if self.save_step_payloads:
                payloads.append(dict(step=st.get("step"), payload=res["payload"]))
            history.append(st)
            if score is not None and score >= self.threshold:
                detection_step = st.get("step")
                break
        return dict(
            case_id=case["case_id"], item_id=case["item_id"],
            gold=case.get("gold"), divergence_step=case.get("divergence_step"),
            trajectory_type=case.get("trajectory_type"),
            detected=detection_step is not None, detection_step=detection_step,
            n_steps_total=len(steps), n_steps_probed=len(step_scores),
            step_scores=step_scores, payloads=payloads, partial=partial,
            meta=meta,
            calls=self.client.calls - c0,
            in_tokens=self.client.in_tokens - t0,
            seconds=self.client.seconds - l0,
        )

def decisions_at_threshold(result, thr):
    """Recompute detection for a threshold from stored step scores (no calls)."""
    for s in result["step_scores"]:
        if s["score"] is not None and s["score"] >= thr:
            return dict(detected=True, detection_step=s["step"], n_steps=s["step"])
    return dict(detected=False, detection_step=None, n_steps=result["n_steps_probed"])