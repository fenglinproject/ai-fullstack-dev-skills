#!/usr/bin/env python3
"""AI Fullstack Skills V4.9 unified CLI.

Defaults are read-only/planned. No model call, repository write, Git push,
LSP startup or test execution without the corresponding explicit opt-in.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

VERSION='5.0'


def parser_factory():
    p=argparse.ArgumentParser(prog='fullstack.py',description='V5.0 unified CLI + lifecycle management + local dashboard')
    p.add_argument('--version',action='version',version='AI Fullstack Dev Skills '+VERSION)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='read-only environment check').add_argument('--project',type=Path)
    r=sub.add_parser('route',help='select skills and execution mode, without executing')
    r.add_argument('--task',required=True)
    r.add_argument('--limit',type=int,default=3)
    r.add_argument('--mode',choices=('light','standard','strict'))
    pr=sub.add_parser('project',help='project state operations')
    ps=pr.add_subparsers(dest='action',required=True)
    for action in ('init','status','add-task','set-task'):
        q=ps.add_parser(action)
        q.add_argument('--project',required=True,type=Path)
        if action=='init':q.add_argument('--force',action='store_true')
        if action=='add-task':
            q.add_argument('--id',required=True);q.add_argument('--title',required=True);q.add_argument('--skill')
        if action=='set-task':
            q.add_argument('--id',required=True);q.add_argument('--status',required=True,choices=('todo','in_progress','blocked','done'))
            q.add_argument('--report');q.add_argument('--manual-reason')
    ix=sub.add_parser('index',help='local source symbol index (no code execution or network)')
    ix.add_argument('--project',type=Path,required=True);ix.add_argument('--query')
    ix.add_argument('--limit',type=int,default=10);ix.add_argument('--save-cache',action='store_true')
    ts=sub.add_parser('select-tests',help='conservative candidate tests; no tests executed')
    ts.add_argument('--project',type=Path,required=True)
    ts.add_argument('--changed',action='append',required=True)
    lsp=sub.add_parser('lsp',help='opt-in trusted LOCAL language server; NOT sandboxed')
    lsp.add_argument('--project',required=True,type=Path)
    lsp.add_argument('--server',type=Path,required=True)
    lsp.add_argument('--server-arg',action='append',default=[])
    lsp.add_argument('--allow-start',action='store_true',help='required: launching arbitrary server is code execution')
    pos=lsp.add_mutually_exclusive_group(required=True)
    pos.add_argument('--query');pos.add_argument('--definition')
    lsp.add_argument('--line',type=int,default=0);lsp.add_argument('--character',type=int,default=0)
    lsp.add_argument('--timeout',type=float,default=10)
    ch=sub.add_parser('check',help='review checks first, execute trusted project tests only with --execute')
    ch.add_argument('--project',type=Path,required=True);ch.add_argument('--name')
    ch.add_argument('--execute',action='store_true');ch.add_argument('--save-report',action='store_true')
    b=sub.add_parser('benchmark',help='read-only pinned independent Git repo benchmark')
    b.add_argument('--project',type=Path,required=True);b.add_argument('--manifest',type=Path,required=True)
    b.add_argument('--repeats',type=int,default=2)
    v=sub.add_parser('verify',help='fixed bundled test matrix; --execute required')
    v.add_argument('--profile',choices=('smoke','full'),default='smoke')
    v.add_argument('--execute',action='store_true')
    v.add_argument('--output',type=Path,help='optional report output path, not a source path')
    cp=sub.add_parser('ci-plan',help='V4.8 planned cross-platform CI suites; no tests run')
    ca=sub.add_parser('ci-aggregate',help='V4.8 strict consistency check of downloaded same-run CI evidence')
    ca.add_argument('--folder',type=Path,required=True)
    ca.add_argument('--expected-sha',required=True)
    ca.add_argument('--run-id',required=True)
    ca.add_argument('--attempt',required=True)
    pack=sub.add_parser('release-package',help='V4.8 deterministic release archive; explicit opt-in')
    opts=pack.add_mutually_exclusive_group(required=True)
    opts.add_argument('--output',type=Path)
    opts.add_argument('--verify',type=Path)
    pack.add_argument('--execute',action='store_true')
    sc=sub.add_parser('supply-chain',help='V5.0 offline dependency/action audit and release provenance')
    sc.add_argument('action',choices=('audit','provenance','verify-provenance','sbom','sign','verify-signature'))
    sc.add_argument('--archive',type=Path)
    sc.add_argument('--output',type=Path)
    sc.add_argument('--statement',type=Path)
    sc.add_argument('--commit')
    sc.add_argument('--run-id')
    sc.add_argument('--private-key',type=Path)
    sc.add_argument('--public-key',type=Path)
    sc.add_argument('--signature',type=Path)
    sc.add_argument('--approve',action='store_true')
    v49=sub.add_parser('release-package-v49',help='V4.9 reproducible package with pinned action and npm lock audits')
    c=v49.add_mutually_exclusive_group(required=True)
    c.add_argument('--output',type=Path)
    c.add_argument('--verify',type=Path)
    v49.add_argument('--execute',action='store_true')
    lc=sub.add_parser('lifecycle',help='V5.0 offline side-by-side install, upgrade, rollback, workspace import')
    lc.add_argument('action',choices=('status','plan','install','upgrade','rollback','import-workspace'))
    lc.add_argument('--home',type=Path,required=True)
    lc.add_argument('--archive',type=Path)
    lc.add_argument('--expected-sha256')
    lc.add_argument('--public-key',type=Path)
    lc.add_argument('--signature',type=Path)
    lc.add_argument('--source',type=Path)
    lc.add_argument('--name')
    lc.add_argument('--approve',action='store_true')
    lc.add_argument('--integrity',action='store_true')
    pack50=sub.add_parser('release-package-v50',help='V5.0 deterministic release package and full verification')
    p50=pack50.add_mutually_exclusive_group(required=True)
    p50.add_argument('--output',type=Path);p50.add_argument('--verify',type=Path)
    pack50.add_argument('--execute',action='store_true')
    rel=sub.add_parser('release-matrix',help='independently isolated, time-bounded bundled Python test shards')
    rel.add_argument('--shard',choices=('core','analysis','platform','collaboration','all'),default='all')
    rel.add_argument('--execute',action='store_true')
    rel.add_argument('--module-timeout',type=float,default=90)
    rel.add_argument('--max-total-seconds',type=float,default=600)
    rel.add_argument('--output',type=Path,help='new JSON report under benchmarks/reports/')
    ar=sub.add_parser('audit-repo',help='read-only Git, task evidence and change record audit')
    ar.add_argument('--project',required=True,type=Path)
    ar.add_argument('--expected-head',help='optional full pinned Git commit SHA')
    ar.add_argument('--require-clean',action='store_true')
    rd=sub.add_parser('repo-readiness',help='V4.4 read-only onboarding, concurrent-change and CI preflight')
    rd.add_argument('--project',required=True,type=Path)
    rd.add_argument('--expected-head',help='optional pinned Git commit SHA')
    rd.add_argument('--require-clean',action='store_true')
    rd.add_argument('--candidate',action='append',default=[],help='candidate file relative to repository; may repeat')
    rd.add_argument('--ci-receipt',type=Path,help='unsigned offline CI JSON (does not attest CI origin)')
    rd.add_argument('--required-check',action='append',default=[])
    rd.add_argument('--require-ci',action='store_true')
    trial=sub.add_parser('repo-trial',help='bounded read-only reliability samples for an existing Git repo')
    trial.add_argument('--project',required=True,type=Path)
    trial.add_argument('--samples',type=int,default=5)
    trial.add_argument('--expected-head')
    trial.add_argument('--require-clean',action='store_true')
    trial.add_argument('--require-ci',action='store_true')
    trial.add_argument('--ci-receipt',type=Path)
    trial.add_argument('--required-check',action='append',default=[])
    cf=sub.add_parser('repo-conflicts',help='read-only overlapping active change detection')
    cf.add_argument('--project',required=True,type=Path)
    cf.add_argument('--candidate',action='append',default=[])
    cf.add_argument('--max-records',type=int,default=1000)
    rc=sub.add_parser('remote-ci',help='opt-in authenticated GitHub CI read; no remote writes')
    rc.add_argument('--project',required=True,type=Path)
    rc.add_argument('--expected-head',required=True)
    rc.add_argument('--required-check',action='append',required=True)
    rc.add_argument('--execute',action='store_true')
    wl=sub.add_parser('worktree-lock',help='human reservation; enforced by participating V4.6 writers')
    wl.add_argument('action',choices=('status','acquire','release'))
    wl.add_argument('--project',required=True,type=Path)
    wl.add_argument('--approve',action='store_true')
    wl.add_argument('--token')
    rec=sub.add_parser('recover',help='diagnose and optionally reconcile interrupted source/Git transactions')
    rec.add_argument('action',choices=('prepared','commit'))
    rec.add_argument('--project',required=True,type=Path)
    rec.add_argument('--change-id',required=True)
    rec.add_argument('--approve',action='store_true')
    rec.add_argument('--worktree-token')
    cmp=sub.add_parser('repo-compare',help='bounded read-only multi-repository sampling')
    cmp.add_argument('--project',required=True,action='append',type=Path)
    cmp.add_argument('--samples',type=int,default=3)
    d=sub.add_parser('dashboard',help='token-gated read-only local web dashboard (127.0.0.1 only)')
    d.add_argument('--project',required=True,type=Path)
    d.add_argument('--port',type=int,default=8765,help='loopback port (0 chooses an ephemeral port)')
    d.add_argument('--open',action='store_true',help='open the local browser explicitly')
    return p


def dispatch(a):
    if a.command=='dashboard':
        from dashboard.server import serve
        return serve(a.project,port=a.port,open_browser=a.open)
    if a.command=='doctor':
        from tools.doctor import diagnose
        return diagnose(a.project)
    if a.command=='route':
        from orchestrator.cli import route
        return route(a.task,a.limit,a.mode)
    if a.command=='project':
        from orchestrator.cli import project_dir,init,status,add_task,set_task
        root=project_dir(str(a.project))
        if a.action=='init':return init(root,a.force)
        if a.action=='status':return status(root)
        if a.action=='add-task':return add_task(root,a.id,a.title,a.skill)
        return set_task(root,a.id,a.status,False,a.report,a.manual_reason)
    if a.command in ('index','select-tests'):
        from tools.incremental_index import build,search
        root=a.project.resolve(strict=True)
        idx=build(root,save_cache=a.save_cache if a.command=='index' else False,
                  use_cache=a.command=='index' and a.save_cache)
        if a.command=='select-tests':
            from tools.test_selection import select
            return select(idx,a.changed)
        return {'schema_version':1,'stats':idx['stats'],
                'search':search(idx,a.query,a.limit) if a.query else None,
                'note':'Local AST locations only; no project code executed or sent to a model.'}
    if a.command=='lsp':
        if not a.allow_start:raise ValueError('local LSP startup requires --allow-start')
        from tools.lsp_client import LSPClient
        with LSPClient(a.project,[str(a.server),*a.server_arg],timeout=a.timeout) as client:
            result=client.workspace_symbols(a.query) if a.query is not None else client.definition(a.definition,a.line,a.character)
        return {'schema_version':1,**result,'note':'TRUSTED local language server was executed. NOT sandboxed.'}
    if a.command=='check':
        from tools.run_checks import run,save_report
        root=a.project.resolve(strict=True)
        if a.save_report and not a.execute:raise ValueError('--save-report requires --execute')
        result=run(root,execute=a.execute,name=a.name)
        if a.save_report:
            result['saved_report']=save_report(root,result)
        return result
    if a.command=='repo-readiness':
        from tools.repo_readiness_v44 import readiness
        return readiness(a.project,expected_head=a.expected_head,require_clean=a.require_clean,
                         candidate_paths=a.candidate,ci_receipt=a.ci_receipt,
                         require_ci=a.require_ci,required_checks=a.required_check)
    if a.command=='repo-trial':
        from tools.repo_trial_v44 import sample
        return sample(a.project,repeats=a.samples,expected_head=a.expected_head,
                      require_clean=a.require_clean,require_ci=a.require_ci,
                      ci_receipt=a.ci_receipt,required_checks=a.required_check)
    if a.command=='repo-conflicts':
        from tools.repo_readiness_v44 import conflicts
        return conflicts(a.project,candidate_paths=a.candidate,max_records=a.max_records)
    if a.command=='repo-compare':
        from tools.repo_comparison_v45 import compare
        return compare(a.project,samples=a.samples)
    if a.command=='remote-ci':
        from tools.remote_ci_v45 import verify
        return verify(a.project,expected_head=a.expected_head,
                      required_checks=a.required_check,execute=a.execute)
    if a.command=='recover':
        from orchestrator.recovery_v46 import recover_prepared,recover_commit
        if a.action=='prepared':
            return recover_prepared(a.project,a.change_id,approved=a.approve,
                                    worktree_token=a.worktree_token)
        return recover_commit(a.project,a.change_id,approved=a.approve,
                              worktree_token=a.worktree_token)
    if a.command=='worktree-lock':
        from tools.worktree_lock_v45 import status,acquire,release
        if a.action=='status':return status(a.project)
        if a.action=='acquire':return acquire(a.project,approved=a.approve)
        return release(a.project,a.token)
    if a.command=='audit-repo':
        from tools.repo_health_v43 import audit
        return audit(a.project,expected_head=a.expected_head,require_clean=a.require_clean)
    if a.command=='benchmark':
        from tools.external_repo_benchmark import evaluate
        return evaluate(a.project,a.manifest,repeats=a.repeats)
    if a.command=='ci-plan':
        from tools.ci_release_v48 import REQUIRED
        return {'required_suites':[{'platform':o,'suite':s} for s,o in sorted(REQUIRED)],
                'actually_executed':False,
                'note':'Planning is not evidence that any OS has passed.'}
    if a.command=='ci-aggregate':
        from tools.ci_release_v48 import aggregate
        return aggregate(a.folder,sha=a.expected_sha.lower(),run_id=a.run_id,attempt=a.attempt)
    if a.command=='release-package':
        from tools.package_release_v48 import make_package,verify_package,files_to_release
        if a.verify is not None:return verify_package(a.verify)
        if not a.execute:return {'planned':True,'output':str(a.output),'files':len(files_to_release())}
        return make_package(a.output)
    if a.command=='supply-chain':
        from tools import supply_chain_v50 as sc
        return sc.run_command(a)
    if a.command=='lifecycle':
        from tools import lifecycle_v50 as lc
        if a.action=='status':return lc.status(a.home,integrity=a.integrity)
        if a.action=='rollback':return lc.rollback(a.home,approve=a.approve)
        if a.action=='import-workspace':
            if a.source is None or a.name is None:raise ValueError('import-workspace requires --source and --name')
            return lc.import_workspace(a.home,a.source,a.name,approve=a.approve)
        if a.archive is None or a.expected_sha256 is None:
            raise ValueError('plan/install/upgrade requires --archive and --expected-sha256')
        if a.action=='plan':
            return lc.plan(a.home,a.archive,a.expected_sha256,public_key=a.public_key,signature=a.signature)
        result=lc.plan(a.home,a.archive,a.expected_sha256,public_key=a.public_key,signature=a.signature)
        if result['action']!=a.action:raise ValueError('requested action does not match installation state')
        return lc.apply(a.home,a.archive,a.expected_sha256,approve=a.approve,
                        public_key=a.public_key,signature=a.signature)
    if a.command=='release-package-v50':
        from tools.package_release_v50 import make_package,verify_package,files_to_release
        if a.verify is not None:return verify_package(a.verify)
        if not a.execute:return {'planned':True,'output':str(a.output),'files':len(files_to_release())}
        return make_package(a.output)
    if a.command=='release-package-v49':
        from tools.package_release_v49 import make_package,verify_package,files_to_release
        if a.verify is not None:return verify_package(a.verify)
        if not a.execute:return {'planned':True,'output':str(a.output),'files':len(files_to_release())}
        return make_package(a.output)
    if a.command=='release-matrix':
        from tools.release_matrix_v47 import run_matrix,save,validate_output
        if a.output and not a.execute:
            raise ValueError('--output requires --execute')
        if a.output:
            validate_output(a.output)
        result=run_matrix(a.shard,execute=a.execute,
                          max_total_seconds=a.max_total_seconds,
                          module_timeout_seconds=a.module_timeout)
        if a.output:save(result,a.output)
        return result
    if a.command=='verify':
        from tools.release_gate import verify
        return verify(profile=a.profile,execute=a.execute,output=a.output)
    raise ValueError('unknown command')


def main(argv=None):
    parser=parser_factory();a=parser.parse_args(argv)
    try:
        result=dispatch(a)
        if a.command!='dashboard':
            print(json.dumps(result,ensure_ascii=False,indent=2))
        # Fail CI when an executed verification detects failures.
        if a.command=='remote-ci' and a.execute and not result['verified']:
            return 1
        if a.command=='repo-trial' and not result['all_reviewable']:
            return 1
        if a.command=='repo-readiness' and result['status']=='blocked':
            return 1
        if a.command=='repo-conflicts' and result['blockers']:
            return 1
        if a.command=='audit-repo' and not result['healthy']:
            return 1
        if a.command=='release-matrix' and a.execute and result['summary']['passed']!=len(result['modules']):
            return 1
        if a.command=='verify' and a.execute and result['summary']['failed']:
            return 1
        if a.command=='check' and a.execute and any(x['status'] in ('failed','error','timeout') for x in result['checks']):
            return 1
        return 0
    except (OSError,ValueError,RuntimeError,TimeoutError,KeyError,json.JSONDecodeError) as e:
        parser.exit(2,'error: '+str(e)+'\n')

if __name__=='__main__':raise SystemExit(main())
