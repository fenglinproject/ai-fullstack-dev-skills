#!/usr/bin/env python3
"""Small offline disposable monorepo exercise + honest timing measurements.

This is a known, generated fixture: never a large real-world repository or an
LLM repair-success benchmark. No network/model calls or project commands.
"""
from __future__ import annotations
import argparse
import json
import tempfile
import time
from pathlib import Path
try:
    from tools.incremental_index import build
    from tools.test_selection import select
    from tools.incremental_graph import analyze
    from tools.monorepo_workspace import discover
except ModuleNotFoundError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.incremental_index import build
    from tools.test_selection import select
    from tools.incremental_graph import analyze
    from tools.monorepo_workspace import discover


def fixture(root:Path, modules:int=24):
    if not 3<=modules<=96:raise ValueError('module count 3..96')
    (root/'package.json').write_text(json.dumps({'name':'v38-fixture','private':True,'workspaces':['packages/*']}))
    for i in range(modules):
        name=f'@fixture/pkg{i:03d}'
        base=root/'packages'/f'pkg{i:03d}'
        (base/'src').mkdir(parents=True)
        (base/'tests').mkdir()
        (base/'package.json').write_text(json.dumps({'name':name,'source':'./src/index.ts'}))
        import_line = '' if i==0 else f"import {{ value as parent }} from '@fixture/pkg{i-1:03d}';\n"
        method='return 1' if i==0 else 'return parent() + 1'
        (base/'src/index.ts').write_text(f'{import_line}export function value(): number {{ {method}; }}\n')
        (base/'tests/index.test.ts').write_text(f"import {{ value }} from '../src/index';\nif(value() <= 0) throw Error('invalid');\n")


def evaluate(modules:int=24)->dict:
    with tempfile.TemporaryDirectory(prefix='ai-v38-bench-') as td:
        root=Path(td)
        fixture(root,modules)
        t0=time.perf_counter_ns()
        initial=build(root,save_cache=True)
        t1=time.perf_counter_ns()
        warm=build(root,save_cache=True)
        t2=time.perf_counter_ns()
        baseline=analyze(root,save=True)
        # Change a leaf dependency; measure only new parse and transitive impact.
        source=root/'packages/pkg000/src/index.ts'
        source.write_text(source.read_text().replace('return 1','return 2'))
        t2_edit=time.perf_counter_ns()
        updated=build(root,save_cache=True)
        t3=time.perf_counter_ns()
        delta=analyze(root,save=True,changed=['packages/pkg000/src/index.ts'])
        cases=select(updated,['packages/pkg000/src/index.ts'])
        expected='packages/pkg001/src/index.ts'
        expected_test='packages/pkg001/tests/index.test.ts'
        assert updated['files'][expected]['dependencies']==['packages/pkg000/src/index.ts']
        assert expected_test in [x['path'] for x in cases['tests']]
        assert expected in [x['path'] for x in delta['affected_dependents']]
        assert warm['stats']['parsed']==0 and updated['stats']['parsed']==1
        return {'schema_version':1,'kind':'generated-visible-fixture','packages':len(discover(root)['packages']),
                'code_files':initial['stats']['files'],
                'cold_parse_count':initial['stats']['parsed'],
                'warm_parse_count':warm['stats']['parsed'],
                'single_edit_parse_count':updated['stats']['parsed'],
                'cold_index_ms':round((t1-t0)/1e6,3),'warm_index_ms':round((t2-t1)/1e6,3),
                'single_edit_index_ms':round((t3-t2_edit)/1e6,3),
                'candidate_tests':len(cases['tests']),
                'candidate_full_suite_required':cases['full_suite_required'],
                'candidate_caution_flags':cases['caution_flags'],
                'edge_delta_count':len(delta['edges_added'])+len(delta['edges_removed']),
                'impact_found':True,'dependency_correct':True,'test_candidate_found':True,
                'caution':'Local timings include disk/cache overhead and depend on machine load; not comparable across environments or real repositories.',
                'model_calls':0}


def paired_comparison(file:Path)->dict:
    """Aggregate *supplied* paired run outcomes. Does not generate test outcomes."""
    if file.is_symlink() or file.stat().st_size > 256*1024:raise ValueError('invalid outcome file')
    raw=json.loads(file.read_text('utf-8'))
    if not isinstance(raw,dict) or raw.get('schema_version')!=1:raise ValueError('invalid paired outcomes')
    cases=raw.get('cases')
    if not isinstance(cases,list) or not 1<=len(cases)<=500:raise ValueError('1..500 paired cases required')
    seen=set();both=only_after=only_before=neither=0
    for case in cases:
        if (not isinstance(case,dict) or not isinstance(case.get('id'),str)
           or len(case['id'])>120 or not case['id'] or case['id'] in seen
           or type(case.get('before_pass')) is not bool or type(case.get('after_pass')) is not bool):
            raise ValueError('each case needs unique id, before_pass and after_pass booleans')
        seen.add(case['id'])
        before,after=case['before_pass'],case['after_pass']
        if before and after:both+=1
        elif before:only_before+=1
        elif after:only_after+=1
        else:neither+=1
    n=len(cases)
    return {'schema_version':1,'source':'user-supplied-paired-outcomes',
            'cases':n,'before_success_rate':round((both+only_before)/n,4),
            'after_success_rate':round((both+only_after)/n,4),
            'improved_cases':only_after,'regressed_cases':only_before,'unchanged_cases':both+neither,
            'absolute_delta':round((only_after-only_before)/n,4),
            'note':'Descriptive comparison only. No model called; input claims are not independently verified.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='V3.8 generated monorepo timing or user-supplied paired outcome analysis')
    p.add_argument('--modules',type=int,default=24)
    p.add_argument('--paired-results',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args(argv)
    try:
        result=paired_comparison(args.paired_results) if args.paired_results else evaluate(args.modules)
        output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if args.output:
            if args.output.is_symlink() or not args.output.parent.is_dir():raise ValueError('unsafe output path')
            args.output.write_text(output,'utf-8')
        print(output)
    except (ValueError,OSError,RuntimeError,AssertionError,KeyError,json.JSONDecodeError) as e:
        p.exit(2,'error: '+str(e)+'\n')
if __name__=='__main__':main()
