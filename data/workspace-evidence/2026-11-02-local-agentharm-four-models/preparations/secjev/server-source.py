"""HTTP bridge preserving SecJev-0.8B v1.0.0 infer.py's FP32, unmerged inference path."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-path', required=True)
    parser.add_argument('--base-path', required=True)
    parser.add_argument('--kev-source', required=True)
    parser.add_argument('--port', type=int, default=8016)
    args = parser.parse_args()
    sys.path.insert(0, args.kev_source)
    import torch
    import peft
    import transformers
    from kev.api import SystemOneRequest, to_record, to_answers
    from kev.checkpoint import Checkpoint, LoadOptions
    from kev.model import rows_of
    from fastapi import FastAPI, Body, HTTPException
    import uvicorn
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    started = time.perf_counter()
    checkpoint = Checkpoint(args.model_path)
    checkpoint.meta.base, checkpoint.meta.base_revision = args.base_path, None
    tokenizer, model = checkpoint.load('cuda:0', LoadOptions(dtype=torch.float32, merge=False, attn='sdpa'))
    torch.cuda.synchronize()
    metadata = {'status': 'ok', 'model': 'secjev08-local', 'context_limit': 8192,
        'hardware': torch.cuda.get_device_name(0), 'torch': torch.__version__, 'transformers': transformers.__version__,
        'peft': peft.__version__, 'dtype': 'float32', 'merge': False, 'attention': 'sdpa_math',
        'tf32': False, 'temperature': model.head.temperature, 'load_seconds': time.perf_counter() - started,
        'server_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'warmup_inferences': 0}
    print(json.dumps(metadata), flush=True)
    app, lock = FastAPI(), threading.Lock()

    @app.get('/health')
    def health():
        return metadata

    @app.post('/v1/systemone')
    def systemone(body: dict = Body(...)):
        if body.get('model') != 'secjev08-local':
            raise HTTPException(400, 'The requested model must match this deployment')
        with lock:
            request = SystemOneRequest.model_validate(body)
            record, meta = to_record(request)
            encoded = model.encode(tokenizer, record, max_state=8192, max_branch=8192, strict=True)
            state, _, branches = rows_of(encoded)
            if any(len(state) + len(branch['ids']) > 8192 for branch in branches):
                raise HTTPException(400, 'State plus question exceeds 8192 tokens; input is not truncated')
            torch.cuda.synchronize()
            started = time.perf_counter()
            with torch.inference_mode():
                logits = model.forward(encoded)
                probabilities = [torch.softmax(z.float(), -1).cpu().tolist() for z in logits]
            torch.cuda.synchronize()
            return {'model': 'secjev08-local', 'answers': to_answers(probabilities, meta),
                'probabilities': {m['id']: dict(zip(m['keys'], p)) for m, p in zip(meta, probabilities)},
                'temperature': model.head.temperature, 'forward_ms': (time.perf_counter() - started) * 1000,
                'usage': {'input_tokens': len(state) + sum(len(b['ids']) for b in branches), 'output_tokens': 0},
                'usage_semantics': 'Packed state and branch token count; non-generative decision head, zero generated tokens'}

    uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='warning')


if __name__ == '__main__':
    main()
