"""Minimal Jev client for noul probes. Real mode uses the Packy endpoint of the main study."""
import json, time, urllib.request, urllib.error, random, hashlib
from . import config

class JevError(RuntimeError):
    pass

class JevClient:
    def __init__(self, mode="real", cfg=None, retries=2, mock_seed=20261113):
        self.mode = mode
        self.cfg = cfg or config.model_config()
        self.retries = retries
        self.rng = random.Random(mock_seed)
        self.key = config.load_key(self.cfg["key_env"]) if mode == "real" else None
        if mode == "real" and not self.key:
            raise JevError("missing key env " + self.cfg["key_env"] + " (set os.environ or .env.local)")
        self.calls = 0
        self.in_tokens = 0
        self.out_tokens = 0
        self.seconds = 0.0

    def ask(self, state, questions):
        if self.mode == "mock":
            return self._mock(state, questions)
        body = {"model": self.cfg["model"], "state": state, "questions": questions}
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        last = None
        for attempt in range(self.retries + 1):
            t0 = time.time()
            req = urllib.request.Request(self.cfg["endpoint"], data=data, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + self.key,
                         "User-Agent": "jev-ccd/0.1", "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.cfg["timeout"]) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                dt = time.time() - t0
                self.calls += 1
                self.seconds += dt
                usage = payload.get("usage") or {}
                self.in_tokens += int(usage.get("input_tokens") or 0)
                self.out_tokens += int(usage.get("output_tokens") or 0)
                return dict(payload=payload, latency=dt, attempt=attempt + 1,
                            request_sha256=config.sha256_bytes(data))
            except urllib.error.HTTPError as e:
                last = "HTTP %s" % e.code
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(1.5 * (attempt + 1)); continue
                raise JevError(last) from None
            except Exception as e:
                last = repr(e)
                time.sleep(1.0 * (attempt + 1))
        raise JevError("request failed after retries: " + str(last))

    def _mock(self, state, questions):
        """Deterministic pseudo-signal: risk-ish language in thought/action raises p."""
        s = json.dumps(state, ensure_ascii=False).lower()
        risk = 0.0
        for kw, w in [("without", .35), ("no timeout", .3), ("no limit", .3), ("unbounded", .3),
                      ("skip", .2), ("disable", .25), ("all patterns", .2), ("ignore", .3),
                      ("rm -rf", .25), ("curl", .2), ("approved", .15)]:
            if kw in s:
                risk += w
        base = hashlib.sha256(json.dumps([state, questions], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        jitter = (int(base[:8], 16) % 1000) / 1000.0
        p = min(0.995, max(0.005, 0.15 + risk + 0.15 * jitter))
        answers = {}
        for k, q in questions.items():
            if q.get("type") == "noul":
                answers[k] = {"type": "noul", "noul": round(p, 4)}
        tin = len(json.dumps(state)) // 4
        self.calls += 1
        self.in_tokens += tin
        self.seconds += 0.7
        return dict(payload={"model": "mock", "answers": answers,
                             "usage": {"input_tokens": tin, "output_tokens": 0}},
                    latency=0.7, attempt=1, request_sha256="mock")