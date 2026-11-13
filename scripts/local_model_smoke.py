import argparse
import json
import statistics
import sys
import time
from pathlib import Path
import torch

root = Path(__file__).resolve().parents[1] / 'local-models'
p = argparse.ArgumentParser()
p.add_argument('model', choices=['plumb', 'decider', 'h2o'])
p.add_argument('--graphs', action='store_true')
args = p.parse_args()
torch.set_num_threads(6)
assert torch.cuda.is_available(), 'CUDA unavailable'
print(torch.__version__, torch.cuda.get_device_name(), torch.cuda.mem_get_info(), flush=True)
start = time.perf_counter()
if args.model == 'plumb':
    sys.path.insert(0, str(root / 'plumb' / 'serve'))
    from plumb_server import Plumb51
    model = Plumb51(str(root / 'weights' / 'plumb-4b'), t1=2.07, tau=-1.0)
    # Official v5 one-read inference. Keep raw calibrated probabilities for experiments.
    def decide(state, question):
        return model.decide(state, question)
elif args.model == 'decider':
    sys.path.insert(0, str(root / 'decider'))
    from decider.infer import Decider
    model = Decider(str(root / 'weights' / 'decider-4b'), device='cuda', use_graphs=args.graphs)
    def decide(state, question):
        return model.system_one(state, {'test': question})['answers']['test']
else:
    # Transformers backend with the v1.1 official shim's prompt/temperature/output functions.
    # This validates local inference, not the official vLLM deployment or benchmark equivalence.
    source = root / 'weights' / 'h2o-lightning-4b-v1.1'
    sys.path.insert(0, str(source))
    import h2o_lightning_shim as shim
    from transformers import AutoTokenizer, Qwen3_5ForCausalLM
    model = Qwen3_5ForCausalLM.from_pretrained(str(source), dtype=torch.bfloat16, device_map={'': 'cuda'}).eval()
    tokenizer = AutoTokenizer.from_pretrained(str(source))
    contract = shim.Contract(json.loads((source/'serve_config.json').read_text()), env={})
    probe = {'type': 'choice', 'instructions': 'Which?', 'criteria': {f'o{i}': f'd{i}' for i in range(len(contract.labels))}}
    probe_text = contract.question_prompt(shim.render_state({'x': 1}, contract.state_compact), probe)[0]
    base_ids = tokenizer.encode(probe_text, add_special_tokens=False)
    label_ids = {}
    for label in contract.labels:
        full = tokenizer.encode(probe_text + ' ' + label, add_special_tokens=False)
        assert len(full) == len(base_ids)+1 and full[:-1] == base_ids, label
        label_ids[label] = full[-1]
    assert len(set(label_ids.values())) == len(label_ids)
    print('Verified official labels:', len(label_ids), flush=True)
    # Match the official fp32 output projection without materializing the full vocabulary logits.
    slot_weight = model.lm_head.weight[list(label_ids.values())].detach().float().contiguous()
    @torch.inference_mode()
    def decide(state, question):
        question = dict(question)
        if question['type'] == 'choice' and isinstance(question['criteria'], list):
            question['criteria'] = {v: v for v in question['criteria']}
        prompt, names, descriptions, labels = contract.question_prompt(shim.render_state(state, contract.state_compact), question)
        ids = tokenizer.encode(prompt, add_special_tokens=False)
        hidden = model.model(input_ids=torch.tensor([ids], device='cuda'), use_cache=False).last_hidden_state[0, -1]
        logits = (hidden.float() @ slot_weight[:len(labels)].T).tolist()
        answer = shim.format_answer(question['type'], names, descriptions, logits, contract.temperature, contract.noul_floor)
        if question['type'] == 'noul':
            answer['raw_noul_before_floor'] = shim.probabilities(logits, contract.temperature)[0]
        answer['input_tokens'] = len(ids)
        return answer
torch.cuda.synchronize()
load_s = time.perf_counter() - start
cases = [
    ('billing', 'My credit card was charged twice for the same purchase. Please refund the duplicate.',
     {'type': 'choice', 'instructions': 'Which team should handle this?', 'criteria': ['billing', 'technical', 'sales']}, 'billing'),
    ('parcel', 'Order #7120 shows delivered to No. 17; the customer lives at No. 71.',
     {'type': 'choice', 'instructions': 'What happened to the parcel?', 'criteria': ['delivered', 'misdelivered', 'unknown']}, 'misdelivered'),
    ('refund', 'Refunds need a receipt and a purchase within 30 days. The customer bought 12 days ago and has no receipt.',
     {'type': 'noul', 'instructions': 'Is a refund permitted under the policy?'}, False),
    ('chinese', '客户的信用卡被同一笔订单重复扣款两次，客户要求退还多扣的款项。',
     {'type': 'choice', 'instructions': '应该由哪个部门处理？', 'criteria': ['账单与退款', '技术支持', '销售咨询']}, '账单与退款'),
    ('score', 'The service is completely unavailable for all customers. Payments cannot be processed.',
     {'type': 'score', 'instructions': 'How severe is this incident?', 'criteria': ['low: cosmetic issue', 'medium: partial degradation', 'high: complete outage']}, 'highest level'),
]
rows = []
for name, state, question, expected in cases:
    latencies = []
    for i in range(4):
        torch.cuda.synchronize()
        start = time.perf_counter()
        answer = decide(state, question)
        torch.cuda.synchronize()
        latencies.append(time.perf_counter() - start)
    row = dict(case=name, expected=expected, answer=answer, first_s=latencies[0], warm_median_s=statistics.median(latencies[1:]))
    rows.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
result = dict(model=args.model, graphs=args.graphs, torch=torch.__version__, gpu=torch.cuda.get_device_name(),
              load_s=load_s, allocated_gib=torch.cuda.max_memory_allocated()/2**30,
              reserved_gib=torch.cuda.max_memory_reserved()/2**30, cases=rows)
if args.model == 'h2o':
    result['backend'] = 'Transformers, official v1.1 shim prompt and formatting; not vLLM'
    result['temperature'] = contract.temperature
    result['noul_floor'] = contract.noul_floor
out = root / ('results-' + args.model + ('-graphs' if args.graphs else '') + '.json')
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('RESULT', out, 'load_s', load_s, 'peak_GiB', result['allocated_gib'], flush=True)
