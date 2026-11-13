"""Native Jev-Guard safety-head bridge; no policy-tree routing or generated verdicts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-path', required=True)
    parser.add_argument('--base-path', required=True)
    parser.add_argument('--port', type=int, default=8027)
    args = parser.parse_args()
    sys.path.insert(0, args.release_path)
    import torch
    import peft
    import transformers
    from jev_inference import JevClassifier
    from fastapi import FastAPI, Body, HTTPException
    import uvicorn
    started = time.perf_counter()
    model = JevClassifier(str(Path(args.release_path) / 'checkpoint'), base_model=args.base_path,
                          device='cuda:0', max_length=16384)
    torch.cuda.synchronize()
    metadata = {'status': 'ok', 'model': 'jev-v3.2-2b', 'context_limit': 16384,
        'hardware': torch.cuda.get_device_name(0), 'torch': torch.__version__,
        'transformers': transformers.__version__, 'peft': peft.__version__,
        'dtype': 'BF16 backbone; FP32 native heads', 'merge': False,
        'tf32_matmul': torch.backends.cuda.matmul.allow_tf32,
        'tf32_cudnn': torch.backends.cudnn.allow_tf32, 'attention': 'sdpa',
        'load_seconds': time.perf_counter() - started, 'warmup_inferences': 0,
        'server_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'native_inference_sha256': hashlib.sha256((Path(args.release_path) / 'jev_inference.py').read_bytes()).hexdigest()}
    print(json.dumps(metadata), flush=True)
    app, lock = FastAPI(), threading.Lock()

    @app.get('/health')
    def health():
        return metadata

    @app.post('/predict')
    def predict(body: dict = Body(...)):
        if (set(body) != {'input', 'options', 'mode', 'safety_applicable'}
                or body['options'] != [] or body['mode'] != 'single' or body['safety_applicable'] is not True):
            raise HTTPException(400, 'This deployment implements the explicit native safety-only contract')
        with lock:
            torch.cuda.synchronize()
            started = time.perf_counter()
            result = model.predict(body['input'], options=[], mode='single', safety_applicable=True)
            torch.cuda.synchronize()
            return {**result, 'latency_ms': (time.perf_counter() - started) * 1000,
                'usage': {'input_tokens': result['prompt_tokens'], 'output_tokens': 0},
                'usage_semantics': 'Native processed prompt tokens; direct safety head with no generated tokens'}

    uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='warning')


if __name__ == '__main__':
    main()
