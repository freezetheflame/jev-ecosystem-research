"""Minimal local HTTP bridge for GLiGuard's GLiNER2 classifier.

Contract used by security_bench.adapters: POST {model,text,schema,...params}
and return the raw classifier dictionary, e.g. {"prompt_safety":"unsafe"}.
"""
import argparse
import time
from typing import Any

import torch
from fastapi import FastAPI, Body
from gliner2 import GLiNER2
import uvicorn

parser = argparse.ArgumentParser()
parser.add_argument('--model-path', default='D:/models/gliguard-300m')
parser.add_argument('--served-name', default='gliguard-300m')
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=8001)
args = parser.parse_args()

model = GLiNER2.from_pretrained(args.model_path)
model.to('cuda' if torch.cuda.is_available() else 'cpu')
app = FastAPI()


@app.get('/health')
def health():
    return {'status': 'ok', 'cuda': torch.cuda.is_available(),
            'device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}


@app.post('/classify')
def classify(body: dict[str, Any] = Body(...)):
    started = time.perf_counter()
    text = body.pop('text')
    body.pop('model', None)
    schema = body.pop('schema')
    result = model.classify_text(text, schema, **body)
    result = dict(result)
    result['latency_seconds'] = time.perf_counter() - started
    return result


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port, log_level='info')
