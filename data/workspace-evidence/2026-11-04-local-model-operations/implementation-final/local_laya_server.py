"""Minimal local HTTP bridge for Laya's System One API.

security_bench sends {model,state,questions,...params}; this bridge calls
Agent.system_one(state, questions) and returns its raw result unchanged.
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
args = parser.parse_args()

agent = Agent(args.model_path, device=args.device)
app = FastAPI()


@app.get('/health')
def health():
    return {'status': 'ok', 'device': str(agent.device), 'cuda': torch.cuda.is_available(),
            'gpu': torch.cuda.get_device_name(0) if agent.device.type == 'cuda' else None,
            'model': args.served_name, 'context_limit': 512, 'torch': torch.__version__,
            'transformers': version('transformers'), 'laya': version('laya'),
            'dtype': str(agent.dtype_for(1)), 'weights_dtype': str(next(agent.model.parameters()).dtype),
            'compile_stub': True, 'warmup_inferences': 0,
            'server_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


@app.post('/v1/systemone')
def systemone(body: dict[str, Any] = Body(...)):
    state = body['state']
    questions = body['questions']
    params = {k: v for k, v in body.items() if k not in ('model', 'state', 'questions')}
    return agent.system_one(state, questions, **params)


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port, log_level='info')
