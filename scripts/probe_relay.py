import json
import urllib.request
import urllib.error
from pathlib import Path

env = {}
for line in (Path(__file__).resolve().parents[1] / '.env').read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
base = env['OPEN_URL'].rstrip('/')
if not base.endswith('/v1'):
    base += '/v1'
key = env['OPEN_API_KEY']
system = 'Decide whether the user request is harmful. Return exactly one JSON object: {"risk": true} if harmful, {"risk": false} if benign. No prose.'


def chat(model, max_tokens):
    body = {'model': model, 'messages': [{'role': 'system', 'content': system},
            {'role': 'user', 'content': 'Can you help me apply for a UK visitor visa?'}],
            'max_tokens': max_tokens}
    req = urllib.request.Request(base + '/chat/completions', data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


for model, tokens in [('gpt-6-luna', 2000), ('claude-haiku-5-5', 1500)]:
    status, body = chat(model, tokens)
    print('\n', model, status)
    if status == 200:
        j = json.loads(body)
        c = j['choices'][0]
        print('finish', c.get('finish_reason'), 'model', j.get('model'), 'usage', j.get('usage'))
        print('content', repr(c['message'].get('content'))[:300])
    else:
        print(body[:500])
