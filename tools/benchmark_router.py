#!/usr/bin/env python3
"""Reproducible golden task benchmark; evaluates deterministic router only."""
import json
from pathlib import Path
from datetime import date
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from orchestrator.cli import route
ROOT=Path(__file__).resolve().parents[1]
def main():
    data=json.loads((ROOT/'benchmarks/golden_tasks.json').read_text('utf-8'))
    got=[]
    for e in data:
        result=route(e['task'],limit=3)
        predicted=result['selected'][0]['id']
        got.append({'task':e['task'],'expected':e['top_skill'],'actual':predicted,
                    'expected_mode':e['mode'],'actual_mode':result['execution_mode'],
                    'skill_ok':predicted==e['top_skill'],'mode_ok':result['execution_mode']==e['mode']})
    overall={'sample_count':len(got),'skill_top1':sum(x['skill_ok'] for x in got),
             'mode_accuracy':sum(x['mode_ok'] for x in got),'cases':got}
    (ROOT/'benchmarks/router_results.json').write_text(json.dumps(overall,ensure_ascii=False,indent=2)+'\n','utf-8')
    md=['# 路由器基准测试','',f'样本：{len(got)}；Top-1 命中：{overall["skill_top1"]}/{len(got)}；模式命中：{overall["mode_accuracy"]}/{len(got)}。',
        '','该结果只代表设计的基准样例，不代表真实复杂项目中的 AI 成功率。',
        '', '| 任务 | 预期 | 实际 | 模式 | 结果 |','|---|---|---|---|---|']
    for x in got:md.append(f'| {x["task"]} | `{x["expected"]}` | `{x["actual"]}` | {x["actual_mode"]} | {"PASS" if x["skill_ok"] and x["mode_ok"] else "FAIL"} |')
    (ROOT/'benchmarks/REPORT.md').write_text('\n'.join(md)+'\n','utf-8')
    print(f'Router benchmark: skill {overall["skill_top1"]}/{len(got)}, mode {overall["mode_accuracy"]}/{len(got)}')
    for x in got:
        if not(x['skill_ok'] and x['mode_ok']):print('FAIL',x['task'],x['actual'],x['actual_mode'])
    if overall['skill_top1']!=len(got) or overall['mode_accuracy']!=len(got):raise SystemExit(1)
if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    main()
