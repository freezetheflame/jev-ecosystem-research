"""Minimal local HTTP bridge for Laya's System One API.

security_bench sends {model,state,questions,...params}; this bridge calls
Agent.predict_long(state, questions) by default (official long-text windowed
scan; falls back to system_one when the state fits one window) and returns
its raw result unchanged.

Long-text split provenance (2026-11-08):
- Current full-local-tsbench-server-v1/laya cell kept intact (7182; ok=3755 failed=3427).
- Failures were ValueError from over-long sequences (e.g. 10594 > 8192 in laya service log).
- Fix path: use Agent.predict_long (laya 0.4.20) instead of system_one for /v1/systemone.
- --no-long-text restores legacy system_one-only behavior.
"""
import argparse
from typing import Any

import torch
# torch 2.2 on Windows has no torch.compile; stub it before transformers imports ModernBert.
torch.compile = lambda *args, **kwargs: (lambda fn: fn)
from fastapi import FastAPI, Body
from laya import Agent
import uvicorn
import hashlib
from pathlib import Path
from importlib.metadata import version

parser = argparse.ArgumentParser()
parser.add_argument('--model-path', default='D:/models/laya')
parser.add_argument('--served-name', default='laya-421m')
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=8002)
parser.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
parser.add_argument('--no-long-text', action='store_true',
                    help='Use Agent.system_one only (legacy; fails on long inputs).')
parser.add_argument('--long-window', type=int, default=None,
                    help='Optional predict_long window override (tokens).')
parser.add_argument('--long-stride', type=int, default=None,
                    help='Optional predict_long stride override (tokens).')
args = parser.parse_args()

agent = Agent(args.model_path, device=args.device)
app = FastAPI()
USE_LONG = not args.no_long_text


@app.get('/health')
def health():
    return {'status': 'ok', 'device': str(agent.device), 'cuda': torch.cuda.is_available(),
            'gpu': torch.cuda.get_device_name(0) if agent.device.type == 'cuda' else None,
            'model': args.served_name, 'context_limit': 512, 'torch': torch.__version__,
            'transformers': version('transformers'), 'laya': version('laya'),
            'dtype': str(agent.dtype_for(1)), 'weights_dtype': str(next(agent.model.parameters()).dtype),
            'compile_stub': True, 'warmup_inferences': 0,
            'long_text_split': USE_LONG, 'long_api': 'predict_long' if USE_LONG else 'system_one',
            'long_window': args.long_window, 'long_stride': args.long_stride,
            'server_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


@app.post('/v1/systemone')
def systemone(body: dict[str, Any] = Body(...)):
    state = body['state']
    questions = body['questions']
    params = {k: v for k, v in body.items() if k not in ('model', 'state', 'questions')}
    if USE_LONG:
        if args.long_window is not None:
            params.setdefault('window', args.long_window)
        if args.long_stride is not None:
            params.setdefault('stride', args.long_stride)
        return agent.predict_long(state, questions, **params)
    return agent.system_one(state, questions, **params)


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port, log_level='info')
