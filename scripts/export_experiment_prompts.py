"""Inventory actual persisted prompts, not reconstructed calls from today's adapter."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import shutil
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from security_bench.common import ROOT,read,rows,write,encode,digest,file_hash


def normalize(request,view):
    bindings={}
    def content(value):
        raw=view.get('user_request')
        try:
            if json.loads(value)==view:
                bindings['{{STATE_JSON}}']=value
                return '{{STATE_JSON}}'
        except (ValueError,TypeError):pass
        if isinstance(raw,str) and value.endswith(raw):
            bindings['{{USER_REQUEST}}']=raw
            return value[:-len(raw)]+'{{USER_REQUEST}}'
        raise ValueError('Cannot safely normalize recorded user content')
    r=json.loads(json.dumps(request))
    if 'state' in r:r['state']=content(r['state'])
    if 'text' in r:r['text']=content(r['text'])
    if isinstance(r.get('input'),str):r['input']=content(r['input'])
    for key in ['messages','input']:
        if isinstance(r.get(key),list):
            for m in r[key]:
                if m.get('role')=='user':m['content']=content(m['content'])
    def restore(v):
        if isinstance(v,str):
            for k,x in bindings.items():v=v.replace(k,x)
            return v
        if isinstance(v,list):return [restore(x) for x in v]
        if isinstance(v,dict):return {k:restore(x) for k,x in v.items()}
        return v
    assert restore(r)==request
    return r,bindings


NOTES={
 'jev':'原生 choice；读取 answers.risk.choice，safe=0、unsafe=1。官方旧通道与新中转使用相同 payload。',
 'd3mini':'官方 System One 原生 choice；不把类别概率改写成生成式回答。',
 'laya':'原生 choice；请求 state 为状态 JSON 字符串，内部编码由 Laya 库处理。',
 'secjev':'官方原生 decision head 的 choice；服务编码 state 与 question/criteria 分支，不生成文本。',
 'jevguard':'input 只包含策略、固定分隔符与原始 user_request。options=[]，mode=single，safety_applicable=true；读取原生 safety 字段，safe=0/unsafe=1，要求 truncated=false，不使用类别结果作为安全判断。',
 'gliguard':'没有手写的 system prompt；原始 user_request 加分类 schema，读取 prompt_safety。threshold 是真实请求参数，保留原值。',
 'shieldstral':'system 限制 yes/no；user 使用 <Instruct>/<Query>/<Document>。当前 query 问是否有害，因此 yes=unsafe、no=safe。max_tokens=1 的 length 结束在该严格协议中允许。',
 'qwen3guard':'当前主版本只提交原始 user_request，不额外加共享 system prompt。Safety: Safe/Unsafe/Controversial 中 Controversial 映射 unsafe。历史 JSON 包装版本单独列出。',
 'qwen35':'system 要求严格 JSON risk，user 为状态 JSON 字符串；risk=true→unsafe，false→safe。关闭 thinking，参数见实际 payload。',
 'gpt6luna':'system 要求严格 JSON risk，user 为状态 JSON 字符串。provider refusal 保留为未决，不能当作模型输出。',
 'claudehaiku':'当前主版本走中转 chat/completions，system 要求严格 JSON risk；早期 smoke 曾使用其他请求参数/协议，历史实际模板另列。'}


def export(out, private):
    out,private=Path(out),Path(private)
    out.mkdir(parents=True,exist_ok=False);private.mkdir(parents=True,exist_ok=False)
    summary=read(ROOT/'data/workspace-evidence/2026-11-03-experiment-summary-v6-final/results.json')
    primary=summary['primary_runs'];root=ROOT/'data/agent-security-study/runs'
    groups={};index=[];configs=[];contracts={};failures=[]
    expanded=private/'expanded-requests.jsonl'
    with expanded.open('x',encoding='utf-8') as full:
        for run in sorted(root.iterdir()):
            if not (run/'effective-config.json').is_file():continue
            config=read(run/'effective-config.json')
            cases={c['case_id']:c for c in rows(run/'cases.jsonl')}
            plans={e['episode_id']:e for e in rows(run/'plan.jsonl')}
            for key,value in config.get('contracts',{}).items():
                cid=digest({'contract':key,'value':value})[:16]
                rec=contracts.setdefault(cid,{'id':cid,'contract':key,'value':value,'config_runs':[],'request_runs':set()})
                rec['config_runs'].append(run.name)
            for arm,model in config['models'].items():
                configs.append({'run':run.name,'arm':arm,'model':model.get('model_id'),'adapter':model.get('adapter',model.get('api')),
                    'parameters':model.get('parameters'),'choice_criteria':model.get('choice_criteria'),
                    'input_field':model.get('input_field'),'controversial_policy':model.get('controversial_policy'),
                    'source':str((run/'effective-config.json').relative_to(ROOT)),'source_sha256':file_hash(run/'effective-config.json')})
            for event in rows(run/'events.jsonl'):
                if event['event']!='request_started':continue
                path=run/event['request_path'];request=read(path)
                assert file_hash(path)==event['request_sha256']
                plan=plans[event['episode_id']];case=cases[plan['case_id']]
                try:template,bindings=normalize(request,case['view'])
                except ValueError as exc:
                    failures.append({'run':run.name,'episode_id':event['episode_id'],'reason':str(exc)});raise
                tid=digest(template)[:16]
                arm=event['model_key']
                group=groups.setdefault(tid,{'id':tid,'template':template,'models':set(),'datasets':set(),'runs':set(),'primary_models':set(),'requests':0})
                group['models'].add(arm);group['datasets'].add(plan['dataset_id']);group['runs'].add(run.name);group['requests']+=1
                if primary.get(arm)==run.name:group['primary_models'].add(arm)
                record={'run':run.name,'arm':arm,'dataset':plan['dataset_id'],'evaluation_mode':plan['evaluation_mode'],
                    'item_id':plan['item_id'],'episode_id':event['episode_id'],'attempt_id':event['attempt_id'],
                    'template_id':tid,'is_primary':primary.get(arm)==run.name,'request_path':str(path.relative_to(ROOT)),
                    'request_sha256':event['request_sha256'],'endpoint':event['endpoint']}
                index.append(record)
                full.write(json.dumps({**record,'request':request,'placeholder_values':bindings},ensure_ascii=False)+'\n')
                def text_leaves(value):
                    if isinstance(value,str):return [value]
                    if isinstance(value,list):return [t for x in value for t in text_leaves(x)]
                    if isinstance(value,dict):return [t for x in value.values() for t in text_leaves(x)]
                    return []
                encoded=text_leaves(request)
                for contract in contracts.values():
                    instruction=contract['value'].get('instructions','')
                    if instruction and any(instruction in text for text in encoded):contract['request_runs'].add(run.name)
    def csvfile(path,records):
        records=list(records);keys=list(dict.fromkeys(k for r in records for k in r))
        with path.open('x',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
            for r in records:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
    for g in groups.values():
        for key in ['models','datasets','runs','primary_models']:g[key]=sorted(g[key])
        write(out/'templates'/f"{g['id']}.json",g)
    for c in contracts.values():c['request_runs']=sorted(c['request_runs'])
    write(out/'contracts.json',list(contracts.values()))
    write(out/'template-catalog.json',list(groups.values()))
    csvfile(out/'request-index.csv',index)
    csvfile(out/'effective-prompt-configs.csv',configs)
    # Copy frozen/native local templates where their source bytes are available.
    native=[]
    for model,key in [('d3mini','d3mini'),('qwen35','qwen35'),('shieldstral','shieldstral'),('jevguard','jevguardbase')]:
        folder=ROOT/'local-models/nov02'/key
        config=read(folder/'tokenizer_config.json')
        template=config.get('chat_template')
        if isinstance(template,str):source=folder/'tokenizer_config.json';text=template
        elif (folder/'chat_template.jinja').is_file():source=folder/'chat_template.jinja';text=source.read_text(encoding='utf-8')
        else:continue
        dest=out/'native-chat-templates'/f'{model}.jinja';dest.parent.mkdir(exist_ok=True);dest.write_text(text,encoding='utf-8')
        native.append({'model':model,'source':str(source.relative_to(ROOT)),'source_sha256':file_hash(source),
            'export_path':str(dest.relative_to(out)),'note':'本地固定制品中的模板；这是内部序列化来源，HTTP实际调用以raw请求为准，不声称API服务端模板已知。'})
    write(out/'native-chat-templates.json',native)
    lines=['# 实验 Prompt 全集','', '整理日期：2026-11-04。来源为本地已运行实验的有效配置、逐请求原件和固定模型制品。此整理没有调用模型。',
        f"共索引 {len(set(r['run'] for r in index))} 个有实际请求的 run、{len(index)} 个实际请求、{len(groups)} 种请求模板；覆盖当前11模型主比较及已保存历史版本、smoke、失败/部分实验。",'',
        '## 占位符和阅读方法','',
        '`{{STATE_JSON}}` 是当次 case.view 经原程序序列化后的完整 JSON 字符串；AgentHarm 主比较结构为 {"user_request":"原始输入"}，不是只发裸文本。',
        '`{{USER_REQUEST}}` 是数据集原始 user_request，保留原换行和 Hint。下方占位符仅为文档展示，实际请求没有这些占位符。原数据内容不在模板文档重复刊载。',
        '每条原请求都验证了文件 SHA256，并验证“模板+原绑定值”可还原同一个 JSON 请求。request-index.csv 逐条关联 run、输入ID、模板ID和原始文件。',
        '请求 payload 含实际生成参数、选项/准则及角色；headers/凭证不属于 prompt，不收录。下面只把确有请求证据的模板列作已使用。', '',
        '## 当前11模型主比较','']
    for arm,name in primary.items():
        model=summary['models'][arm]
        lines += [f"### {model['display_name']}",'',f"主 run：`{name}`。{NOTES[arm]}",'']
        selected=[g for g in groups.values() if arm in g['primary_models']]
        assert selected
        for g in selected:
            lines += [f"实际模板 ID：`{g['id']}`；完整请求：",'','```json',json.dumps(g['template'],ensure_ascii=False,indent=2),'```','']
    lines += ['## 其他已使用模板与历史差异','',
        '下列模板覆盖已保存的所有真实请求，包含早期多基准 smoke（InjecAgent 输入检查、TS-Bench 执行前判断、ATBench 完整轨迹判断）。这些 smoke 的提示不代表已完成相应全量基准。',
        '同一策略在不同 max_tokens、格式、模型名或 schema 下会产生不同模板ID，因此这里保留请求层面的差异。Jev 官方与中转 payload 相同，端点差异见 request-index.csv。','']
    for g in groups.values():
        if g['primary_models']:continue
        lines += [f"### 历史模板 {g['id']}",'',f"模型：{', '.join(g['models'])}；数据集：{', '.join(g['datasets'])}；请求数：{g['requests']}。",'',
            '来源 run：'+', '.join(f'`{x}`' for x in g['runs']), '','```json',json.dumps(g['template'],ensure_ascii=False,indent=2),'```','']
    lines += ['## 原生内部编码与可见边界','',
        'D3-Mini、Qwen3.5、Shieldstral、Jev-Guard 的本地 chat template 原文另存 native-chat-templates/*.jinja，出处与hash见 native-chat-templates.json。HTTP角色消息与内部加入的特殊token属于两层，不能把模板来源文件当作已保存的每次 input_ids。',
        'Jev-Guard 原生处理调用：processor.apply_chat_template([{role:user, content:input}], tokenize=True, return_dict=True, return_tensors=pt, add_generation_prompt=True, enable_thinking=False)。',
        'Qwen3.5 与 Shieldstral 服务调用 tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, **chat_template_kwargs)，再 tokenize(add_special_tokens=False,truncation=False)。其他本地分类器的额外内部编码按原生库实现；未取得本轮冻结模板或完整token序列的部分不补造。',
        'Jev、GPT和Claude中转API的服务端内部system提示/分词模板未公开在本轮返回中；这里整理的是我们实际发送的请求。Qwen3Guard历史服务的内部chat template未在此次可读固定制品中取得，HTTP消息内容已完整整理。', '',
        '## 配置里的策略与复现','',
        'contracts.json 保留全部有效配置里的原文 instructions、标签语义和正类定义，并区分出现在实际请求中的 run 与仅存在于配置中的 run。配置存在不等于已实际执行。',
        '逐条展开的完整请求（含数据集输入）和占位符绑定另存本地整理包 expanded-requests.jsonl；模板文档、模板JSON、CSV索引、内部模板和逐条原文一起打包。原始 run/raw 不做修改。',
        '复现：python scripts/export_experiment_prompts.py --out <新模板目录> --private <新展开请求目录>。不发起模型调用。']
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    counts={'runs':len(set(r['run'] for r in index)),'requests':len(index),'templates':len(groups),'primary_models':len(primary),
        'exact_payload_hash_checks':len(index),'lossless_template_roundtrip_checks':len(index),'model_calls':0}
    write(out/'verification.json',counts)
    write(out/'SHA256SUMS.json',{p.relative_to(out).as_posix():file_hash(p) for p in out.rglob('*') if p.is_file()})
    write(private/'expanded-request-manifest.json',{'file':'expanded-requests.jsonl','sha256':file_hash(expanded),'requests':len(index),'contains_original_dataset_inputs':True,'credentials_included':False})
    print(json.dumps(counts,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--private',required=True);a=p.parse_args();export(a.out,a.private)
