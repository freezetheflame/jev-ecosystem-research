"""Paths, Jev endpoint config, and secret loading (never prints key values)."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN = os.path.join(ROOT, "data", "agent-security-study", "runs", "full-api-jev-packy-v1", "jev", "stepshield")
MODEL_CFG = os.path.join(ROOT, "configs", "full-suite-models.packy-v1.json")
ENV_FILE = os.path.join(ROOT, ".env.local")
OUT_ROOT = os.path.join(ROOT, "rq1", "architecture-2026-11-13", "runs")

def load_key(name="PACKY_AI_KEY"):
    v = os.environ.get(name)
    if v:
        return v
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def model_config():
    cfg = json.load(open(MODEL_CFG, encoding="utf-8"))
    m = cfg["models"]["jev"]
    return dict(endpoint=m["endpoint"], model=m["model_id"], key_env=m["api_key_env"],
                timeout=m.get("timeout_seconds", 120), price_in_per_token=0.042 / 1e6)

def sha256_bytes(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()
