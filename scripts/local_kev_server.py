"""Pinned native Kev choice bridge: explicit BF16 unmerged, no cross-request cache."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model-path', required=True)
    p.add_argument('--base-path', required=True)
    p.add_argument('--kev-source', required=True)
    p.add_argument('--port', type=int, default=8028)
    args = p.parse_args()
    sys.path.insert(0, args.kev_source)
    import torch
    import transformers
    import peft
    from kev.api import SystemOneRequest, to_record, to_answers
    from kev.checkpoint import Checkpoint, LoadOptions
    from kev.model import rows_of
    from fastapi import FastAPI, Body, HTTPException
    import uvicorn
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    started = time.perf_counter()
    ck = Checkpoint(args.model_path)
    original_base = ck.meta.base
    original_revision = ck.meta.base_revision
    ck.meta.base, ck.meta.base_revision = args.base_path, None
    options = LoadOptions(dtype=torch.bfloat16, merge=False, attn='sdpa',
                          backend='torch', cuda_graphs=False, fused=False,
                          lora_scale=1.0, temperature=None)
    tokenizer, model = ck.load('cuda:0', options)
    torch.cuda.synchronize()
    metadata = {'status': 'ok', 'model': 'kev-4b-local', 'context_limit': 8192,
        'hardware': torch.cuda.get_device_name(0), 'torch': torch.__version__,
        'transformers': transformers.__version__, 'peft': peft.__version__,
        'dtype': 'BF16 backbone; FP32 native pointer head', 'merge': False,
        'temperature': model.head.temperature, 'original_base': original_base,
        'original_base_revision': original_revision, 'attention': 'sdpa',
        'fused': False, 'cuda_graphs': False, 'tf32': False,
        'cross_request_prefix_cache': False, 'date_facts': False,
        'load_seconds': time.perf_counter() - started, 'warmup_inferences': 0,
        'server_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    print(json.dumps(metadata), flush=True)
    app, lock = FastAPI(), threading.Lock()

    @app.get('/health')
    def health():
        return metadata

    @app.post('/v1/systemone')
    def systemone(body: dict = Body(...)):
        if body.get('model') != 'kev-4b-local':
            raise HTTPException(400, 'Model must match this deployment')
        with lock:
            req = SystemOneRequest.model_validate(body)
            record, meta = to_record(req)
            encoded = model.encode(tokenizer, record, max_state=8192, max_branch=8192, strict=True)
            state, _, branches = rows_of(encoded)
            if any(len(state) + len(b['ids']) > 8192 for b in branches):
                raise HTTPException(400, 'State plus question exceeds 8192; no truncation')
            torch.cuda.synchronize()
            started = time.perf_counter()
            with torch.inference_mode():
                logits = model.forward(encoded)
                probabilities = [torch.softmax(z.float(), -1).cpu().tolist() for z in logits]
            torch.cuda.synchronize()
            return {'model': 'kev-4b-local', 'answers': to_answers(probabilities, meta),
                'probabilities': {m['id']: dict(zip(m['keys'], v)) for m, v in zip(meta, probabilities)},
                'temperature': model.head.temperature, 'truncated': False,
                'forward_ms': (time.perf_counter() - started) * 1000,
                'usage': {'input_tokens': len(state) + sum(len(b['ids']) for b in branches), 'output_tokens': 0},
                'usage_semantics': 'Encoded state plus question branches; non-generative head'}

    uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='warning')


if __name__ == '__main__':
    main()
