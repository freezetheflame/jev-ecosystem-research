import json
from transformers import AutoTokenizer
p='D:/models/gliguard-300m'
t=AutoTokenizer.from_pretrained(p, extra_special_tokens={})
run='D:/projects/jev_empirical/jev-ecosystem-research/data/agent-security-study/runs/2026-11-01-agentharm-gliguard-50/cases.jsonl'
rows=[json.loads(l) for l in open(run,encoding='utf-8') if l.strip()]
lens=sorted(len(t(x['view']['user_request'], add_special_tokens=True)['input_ids']) for x in rows)
print('n',len(lens),'max',lens[-1],'p95',lens[int(0.95*len(lens))-1],'over512',sum(1 for x in lens if x>512),'over256',sum(1 for x in lens if x>256))
