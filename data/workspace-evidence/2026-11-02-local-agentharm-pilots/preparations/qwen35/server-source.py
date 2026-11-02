"""Serial Transformers bridge for explicit Qwen3.5/Shieldstral local pilot configurations."""
import argparse
import hashlib
import json
from pathlib import Path
import threading
import time
import uuid


def completion_reason(generated, eos_ids, limit):
    eos_ids = eos_ids if isinstance(eos_ids, (list, tuple)) else [eos_ids]
    return 'stop' if (generated and generated[-1] in eos_ids) or len(generated) < limit else 'length'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-path', required=True)
    parser.add_argument('--served-name', required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--context-limit', type=int, default=32768)
    args = parser.parse_args()
    import torch
    import transformers
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, ConfigDict
    import uvicorn
    load_start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    model = AutoModelForImageTextToText.from_pretrained(args.model_path, local_files_only=True,
        dtype=torch.bfloat16, device_map={'': 'cuda:0'}, attn_implementation='sdpa')
    model.eval()
    torch.cuda.synchronize()
    metadata = {'status': 'ok', 'model': args.served_name, 'model_path': str(Path(args.model_path).resolve()),
                'hardware': torch.cuda.get_device_name(0), 'torch': torch.__version__,
                'transformers': transformers.__version__, 'dtype': 'bfloat16',
                'attention': 'sdpa', 'context_limit': args.context_limit,
                'server_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'load_seconds': time.perf_counter() - load_start, 'warmup_inferences': 0}
    print(json.dumps(metadata), flush=True)
    app, lock = FastAPI(), threading.Lock()

    class ChatRequest(BaseModel):
        model_config = ConfigDict(extra='forbid')
        model: str
        messages: list[dict]
        max_tokens: int
        temperature: float = 0.0
        chat_template_kwargs: dict = {}

    @app.get('/health')
    def health():
        return metadata

    @app.post('/v1/chat/completions')
    def chat(body: ChatRequest):
        if body.model != args.served_name or body.temperature != 0 or body.max_tokens <= 0:
            raise HTTPException(400, 'Model must match deployment; only explicit greedy generation is supported')
        if set(body.chat_template_kwargs) - {'enable_thinking'}:
            raise HTTPException(400, 'Unsupported chat template options')
        with lock:
            started = time.perf_counter()
            text = tokenizer.apply_chat_template(body.messages, tokenize=False, add_generation_prompt=True,
                                                **body.chat_template_kwargs)
            inputs = tokenizer(text, return_tensors='pt', add_special_tokens=False, truncation=False)
            length = int(inputs['input_ids'].shape[1])
            if length + body.max_tokens > args.context_limit:
                raise HTTPException(400, 'Input exceeds configured context; no truncation performed')
            inputs = inputs.to('cuda:0')
            with torch.inference_mode():
                output = model.generate(**inputs, max_new_tokens=body.max_tokens, do_sample=False,
                                        pad_token_id=tokenizer.eos_token_id, use_cache=True)
            torch.cuda.synchronize()
            generated = output[0][length:].tolist()
            content = tokenizer.decode(generated, skip_special_tokens=True)
            reason = completion_reason(generated, model.generation_config.eos_token_id, body.max_tokens)
            return {'id': 'chatcmpl-' + uuid.uuid4().hex, 'object': 'chat.completion',
                    'created': int(time.time()), 'model': args.served_name,
                    'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': content}, 'finish_reason': reason}],
                    'usage': {'prompt_tokens': length, 'completion_tokens': len(generated),
                              'total_tokens': length + len(generated)},
                    'latency_seconds': time.perf_counter() - started,
                    'effective_generation': {'do_sample': False, 'max_new_tokens': body.max_tokens,
                                             'chat_template_kwargs': body.chat_template_kwargs}}

    uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='warning')


if __name__ == '__main__':
    main()
