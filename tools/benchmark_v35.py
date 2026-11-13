#!/usr/bin/env python3
"""Reproducible *local fixture* benchmark for lexical retrieval and repair triage.

Never runs project source, installs dependencies or sends code over the network.
Scores fixed, human-labeled examples; not a claim of live-model success rates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from tools.context_retrieval import retrieve
    from tools.failure_triage import classify
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.context_retrieval import retrieve
    from tools.failure_triage import classify

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'benchmarks/v35_cases.json'


def evaluate(root:Path=ROOT,fixtures:Path=FIXTURES,top_k:int=3)->dict:
    if not isinstance(top_k,int) or isinstance(top_k,bool) or not 1<=top_k<=12:
        raise ValueError('top_k must be 1..12')
    raw=fixtures.read_bytes()
    doc=json.loads(raw)
    if doc.get('schema_version')!=1:raise ValueError('unsupported benchmark schema')
    retrieval=[]; triage=[]
    for entry in doc['retrieval_cases']:
        rel=Path(entry['project'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe benchmark project path')
        project=(root/rel).resolve(strict=True)
        if project!=root and root not in project.parents:raise ValueError('project outside benchmark root')
        out=retrieve(project,entry['task'],top_k,include_snippets=False)
        paths=[r['path'] for r in out['results']]
        rank=paths.index(entry['expected_file'])+1 if entry['expected_file'] in paths else None
        retrieval.append({'id':entry['id'],'project':entry['project'],
                          'expected_file':entry['expected_file'],'top_paths':paths,
                          'rank':rank,'recall_at_k':rank is not None})
    for entry in doc['failure_cases']:
        actual=classify(entry['diagnostic'])['category']
        triage.append({'id':entry['id'],'expected':entry['category'],
                       'actual':actual,'correct':entry['category']==actual})
    hits=sum(v['recall_at_k'] for v in retrieval)
    top1=sum(v['rank']==1 for v in retrieval)
    correct=sum(v['correct'] for v in triage)
    return {'schema_version':1,'fixture_sha256':hashlib.sha256(raw).hexdigest(),
            'top_k':top_k,'retrieval':{'cases':len(retrieval),'recall_hits':hits,
            'recall_at_k':round(hits/len(retrieval),4) if retrieval else None,
            'top1_hits':top1,'top1_accuracy':round(top1/len(retrieval),4) if retrieval else None,
            'mrr_at_k':round(sum(1/v['rank'] for v in retrieval if v['rank'])/len(retrieval),4) if retrieval else None,
            'per_project':{name:{'cases':sum(x['project']==name for x in retrieval),
                                  'hits':sum(x['project']==name and x['recall_at_k'] for x in retrieval)}
                           for name in sorted({x['project'] for x in retrieval})}, 'cases_detail':retrieval},
            'triage':{'cases':len(triage),'correct':correct,
                      'accuracy':round(correct/len(triage),4) if triage else None,
                      'cases_detail':triage},
            'note':'Small curated offline fixtures; measures candidate retrieval and heuristic triage only, NOT autonomous code repair, model quality, CI reliability or production readiness.'}


def compare(current:dict,baseline:dict)->dict:
    result={}
    for section,key in (('retrieval','recall_at_k'),('retrieval','top1_accuracy'),
                        ('retrieval','mrr_at_k'),('triage','accuracy')):
        curr=current[section][key];prev=baseline[section][key]
        result[f'{section}.{key}']={'baseline':prev,'current':curr,
            'delta':round(curr-prev,4) if curr is not None and prev is not None else None}
    result['comparable_fixtures']=current.get('fixture_sha256')==baseline.get('fixture_sha256')
    result['note']='Different fixtures invalidate direct performance comparisons.'
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description='Offline cross-project benchmark: no model or network')
    p.add_argument('--top-k',type=int,default=3)
    p.add_argument('--fixtures',type=Path,default=FIXTURES)
    p.add_argument('--output',type=Path,help='optional JSON report location')
    p.add_argument('--baseline',type=Path,help='optional prior JSON report for comparison')
    p.add_argument('--min-recall',type=float,default=0.8)
    p.add_argument('--min-triage',type=float,default=0.8)
    a=p.parse_args(argv)
    try:
        if not 0<=a.min_recall<=1 or not 0<=a.min_triage<=1:raise ValueError('thresholds must be in [0, 1]')
        result=evaluate(ROOT,a.fixtures,a.top_k)
        if a.baseline:result['comparison']=compare(result,json.loads(a.baseline.read_text('utf-8')))
        body=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if a.output:
            if a.output.is_symlink():raise ValueError('symlink output forbidden')
            a.output.write_text(body,'utf-8')
        print(body)
        if result['retrieval']['recall_at_k']<a.min_recall or result['triage']['accuracy']<a.min_triage:
            raise SystemExit(1)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        p.exit(2,f'error: {e}\n')


if __name__=='__main__':main()
