"""Minimal local OpenAI-compatible server for Qwen3Guard-Gen.

Only the fields used by security_bench are implemented: /v1/models and
/v1/chat/completions. It applies the checkpoint chat template and returns the
generated text verbatim, so the client-side Safety: parser remains authoritative.
"""
import argparse
import time
import uuid
from typing import Any

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import uvicorn
import hashlib
from pathlib import Path
from importlib.metadata import version
from local_remaining_server import completion_reason

parser = argparse.ArgumentParser()
parser.add_argument('--model-path', default='D:/models/qwen3guard-0.6b')
parser.add_argument('--served-name', default='qwen3guard-0.6b')
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=8000)
args = parser.parse_args()

tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    args.model_path, torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map='auto', trust_remote_code=True)
model.eval()

app = FastAPI()


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]]
    max_tokens: int = 64
    temperature: float | None = None
    top_p: float | None = None


@app.get('/v1/models')
def models():
    return {'object': 'list', 'data': [{'id': args.served_name, 'object': 'model', 'owned_by': 'local'}]}


@app.get('/health')
def health():
    return {'status': 'ok', 'cuda': torch.cuda.is_available(),
            'device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu',
            'model': args.served_name, 'context_limit': model.config.max_position_embeddings,
            'torch': torch.__version__, 'transformers': version('transformers'),
            'dtype': str(model.dtype), 'warmup_inferences': 0,
            'server_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


@app.post('/v1/chat/completions')
def chat(body: ChatRequest):
    if body.model not in (None, args.served_name):
        raise HTTPException(400, 'Requested model must match this deployment')
    if body.max_tokens <= 0 or body.temperature not in (None, 0, 0.0):
        raise HTTPException(400, 'Only explicit greedy generation is supported')
    started = time.perf_counter()
    messages = body.messages
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors='pt', truncation=False).to(model.device)
    limit = model.config.max_position_embeddings
    if inputs['input_ids'].shape[1] + body.max_tokens > limit:
        raise HTTPException(400, 'Full input plus output exceeds context; no truncation')
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=body.max_tokens, do_sample=False,
                                pad_token_id=tokenizer.eos_token_id)
    generated = output[0][inputs['input_ids'].shape[1]:]
    content = tokenizer.decode(generated, skip_special_tokens=True)
    reason = completion_reason(generated.tolist(), model.generation_config.eos_token_id, body.max_tokens)
    return {
        'id': 'chatcmpl-' + uuid.uuid4().hex,
        'object': 'chat.completion',
        'created': int(time.time()),
        'model': body.model or args.served_name,
        'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': content},
                     'finish_reason': reason}],
        'usage': {'prompt_tokens': int(inputs['input_ids'].shape[1]),
                  'completion_tokens': int(generated.shape[0]),
                  'total_tokens': int(inputs['input_ids'].shape[1] + generated.shape[0])},
        'latency_seconds': time.perf_counter() - started,
    }


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port, log_level='info')
