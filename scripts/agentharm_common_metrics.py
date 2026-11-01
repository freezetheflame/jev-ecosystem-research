"""Common-item comparison and coverage bounds for the relay pilot."""
import argparse, json, math, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security_bench.common import read, rows, write


def wilson(k, n, z=1.959963984540054):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z*z/n; c = (p + z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [max(0, c-h), min(1, c+h)]


def metrics(pairs):
    tp=sum(1 for g,p in pairs if g==1 and p==1); fp=sum(1 for g,p in pairs if g==0 and p==1)
    tn=sum(1 for g,p in pairs if g==0 and p==0); fn=sum(1 for g,p in pairs if g==1 and p==0)
    n=tp+fp+tn+fn
    div=lambda a,b: None if b==0 else a/b
    return {'N':n,'TP':tp,'FP':fp,'TN':tn,'FN':fn,'accuracy':div(tp+tn,n),
            'accuracy_wilson95':wilson(tp+tn,n),'precision':div(tp,tp+fp),
            'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn),'fpr':div(fp,fp+tn),
            'fnr':div(fn,fn+tp),'specificity':div(tn,tn+fp)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True); a=ap.parse_args()
    run=Path(a.run_dir).resolve(); cfg=read(run/'effective-config.json'); arms=cfg['evaluation_models']
    ep=rows(run/'episodes.jsonl'); plan=rows(run/'plan.jsonl')
    valid=[e for e in ep if e['status']=='ok' and e.get('prediction') is not None]
    # item -> arm -> repeat -> prediction
    votes=defaultdict(lambda: defaultdict(dict)); gold={}
    for e in valid:
        votes[e['item_id']][e['arm']][e['repeat']]=e['prediction']; gold[e['item_id']]=e['gold']
    common=sorted(i for i in votes if all(votes[i].get(arm) for arm in arms))
    out={'record_kind':'derived_common_item_metrics_not_confirmatory','created_at':datetime.now(timezone.utc).isoformat(),
         'run_dir':str(run),'arms':{},'common_items':len(common),'refusals':{},'bounds':{}}
    for arm in arms:
        maj={i: 1 if sum(votes[i][arm].values()) > len(votes[i][arm])/2 else 0 for i in common}
        pairs=[(gold[i],maj[i]) for i in common]
        per_rep={}
        for rep in sorted({r for i in common for r in votes[i][arm]}):
            rp=[(gold[i],votes[i][arm][rep]) for i in common if rep in votes[i][arm]]
            per_rep[str(rep)]=metrics(rp)
        out['arms'][arm]={'majority_common':metrics(pairs),'per_repeat_common':per_rep,
                          'common_n':len(common)}
        refused=[e for e in ep if e['arm']==arm and e['status']=='provider_policy_refusal']
        failed=[e for e in ep if e['arm']==arm and e['status'] not in ('ok','provider_policy_refusal')]
        out['refusals'][arm]={'provider_refusals':len(refused),
            'failed_other':len(failed),
            'refused_items':sorted({e['item_id'] for e in refused}),
            'failed_items':sorted({(e['item_id'],e['repeat'],e.get('error_type')) for e in failed}, key=str)}
    # bounds over all 50 items for arms with non-scorable items (best/worst case)
    all_items=sorted(gold)
    for arm in arms:
        maj={i:(1 if sum(votes[i][arm].values()) > len(votes[i][arm])/2 else 0) for i in all_items if i in votes and votes[i][arm]}
        scorable=len(maj); correct=sum(1 for i in maj if maj[i]==gold[i])
        missing=len(all_items)-scorable
        out['bounds'][arm]={'all_items':len(all_items),'scorable_items':scorable,'correct':correct,
                            'missing_unanimous':missing,
                            'accuracy_best_if_missing_correct':(correct+missing)/len(all_items),
                            'accuracy_worst_if_missing_wrong':correct/len(all_items)}
    out_dir=run/'analysis'/(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S_%f_0000')+'-common-metrics')
    out_dir.mkdir(parents=True, exist_ok=False)
    write(out_dir/'common-metrics.json', out)
    lines=['# Relay pilot：共同 item 与覆盖率边界','',f"共同 item = {len(common)}；总 item = {len(all_items)}。",'']
    for arm in arms:
        m=out['arms'][arm]['majority_common']; ci=m['accuracy_wilson95']
        fmt=lambda v: 'NA' if v is None else f"{v:.3f}"
        lines+= [f"## {arm}", '', f"共同 {len(common)} item 多数票：N={m['N']} TP={m['TP']} FP={m['FP']} TN={m['TN']} FN={m['FN']} accuracy={fmt(m['accuracy'])} [{fmt(ci[0])}, {fmt(ci[1])}] precision={fmt(m['precision'])} recall={fmt(m['recall'])} F1={fmt(m['f1'])} FPR={fmt(m['fpr'])}", '']
        b=out['bounds'][arm]
        lines+= [f"全 50 item 覆盖：可判 {b['scorable_items']}/50；若缺失全对 accuracy={b['accuracy_best_if_missing_correct']:.3f}，若缺失全错 accuracy={b['accuracy_worst_if_missing_wrong']:.3f}。", '']
        r=out['refusals'][arm]
        lines+= [f"provider refusal={r['provider_refusals']}，其他失败={r['failed_other']}；refused items={r['refused_items']}。", '']
    (out_dir/'common-metrics.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(out_dir),'common':len(common),'arms':out['arms'],'refusals':out['refusals'],'bounds':out['bounds']},ensure_ascii=False,indent=2))


if __name__=='__main__': main()