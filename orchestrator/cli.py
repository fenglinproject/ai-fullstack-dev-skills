#!/usr/bin/env python3
"""Safe, stdlib-only CLI for deterministic skill routing and project status.

This tool *recommends* skills and persists task metadata. It does NOT run an LLM,
modify business code, or authorize privileged deployment actions.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import os
import hashlib
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROUTES=ROOT/'skill_routing_matrix.json'
PRIMARY=ROOT/'orchestrator'/'primary_skills.json'
SENSITIVE=[
 ('payment',('支付','退款','金额','订单资金','回调验签','库存扣减','余额扣减','payment','refund','checkout','inventory deduction')),
 ('identity',('登录','注册','认证','鉴权','权限','rbac','oauth','token','密码','会话','越权','auth')),
 ('privacy',('隐私','敏感数据','个人信息','泄露','脱敏','secret','credential','隐私数据')),
 ('database',('数据库迁移','删表','删字段','删除数据','生产库','数据迁移','migration','drop table','truncate','schema change')),
 ('production',('生产部署','上线','发布生产','线上环境','生产环境','回滚','production','hotfix','deploy prod')),
 ('upload',('文件上传','私有文件','上传接口','file upload')),
]
HIGH_ACTIONS=('修改','实现','开发','新增','重构','迁移','执行','删除','部署','上线','接入','修复','写','设计','制作','生成','创建','规划','change','implement','build','migrate','deploy','update','delete','fix','create','write')
ANALYSIS_ONLY=('解释','理解','介绍','什么是','科普','比较','优缺点','讲解','分析一下','如何理解','explain','what is')
TRIVIAL=('按钮颜色','颜色','css','样式','文案','拼写','微调','spacing','color','typo','readme排版')

def normalized(s:str)->str:
    return re.sub(r'\s+','',s.casefold())

# Task intent takes priority over incidental domain nouns ("登录页" != authentication change).
_UI_EDIT = re.compile(r'(按钮|页面|网页|表单|css|样式|颜色|色值|间距|字体|排版|布局|padding|spacing|button|style)', re.I)
_UI_OPERATION = re.compile(r'(改|调整|修改|微调|优化|修复|美化|设置|change|adjust|fix|update|tweak)', re.I)
_UI_PRESENTATION = re.compile(r'(css|样式|颜色|色值|间距|字体|排版|布局|padding|spacing|color|style|蓝色)', re.I)
_SENSITIVE_MUTATION = re.compile(r'(鉴权逻辑|认证逻辑修改|修改认证|修改权限|权限校验|支付逻辑|支付接口|支付回调|退款接口|生产部署|正式上线|数据库迁移|执行迁移|删表|删除用户|更改表结构|修改表结构|数据清除|密钥泄露)', re.I)
_NEGATED = re.compile(r'(?:不(?:要|需要|得)?|不要|禁止|避免|无需)(?:改|动|碰|修改|调整|操作|处理|涉及|改变|触碰)(?:任何)?(?:后端|数据库|认证逻辑|鉴权逻辑|支付逻辑|权限|接口)', re.I)
_ANALYSIS_PREFIX = re.compile(r'^(?:请)?(?:解释|介绍|讲解|概述|科普|分析一下|比较|how does|what is|explain|describe)')
_SPECIALIZED = [
    (re.compile(r'(next\.?js|nuxt|vite|react|vue|前端项目|web app|网页应用)', re.I),'frontend.frontend_project_init'),
    (re.compile(r'(微信小程序|小程序|uni-?app|mini.?program|wxml)', re.I),'frontend.miniprogram_config_generator'),
    (re.compile(r'(kubernetes|\bk8s\b|helm|容器编排)', re.I),'architecture.logging_monitoring_plan'),
]


def ui_only(task: str)->bool:
    # This is a conservative classifier for presentation-only work, not generic UI security work.
    return (bool(_UI_EDIT.search(task) and _UI_OPERATION.search(task) and _UI_PRESENTATION.search(task))
            and not _SENSITIVE_MUTATION.search(_NEGATED.sub('',task)))


def effective_text(task: str)->str:
    # Negated scopes are never treated as requested mutations.
    return _NEGATED.sub('',task)


def load():
    data=json.loads(ROUTES.read_text(encoding='utf-8'))
    return {r['id']:r for r in data}


def risk_for(task:str, skill:dict, requested:str|None=None):
    q=normalized(effective_text(task))
    hits=[name for name, terms in SENSITIVE if any(normalized(t) in q for t in terms)]
    actionable=any(normalized(t) in q for t in HIGH_ACTIONS)
    explanation=bool(_ANALYSIS_PREFIX.search(task.strip().casefold()))
    if re.search(r'(?:修改|更改|删除|重建|alter|drop).*?(?:生产|线上|数据库).*?(?:表结构|字段|数据表|schema)|(?:生产库|production database).*(?:修改|迁移|删除|alter)',task,re.I):
        level='high'
    elif ui_only(task):
        level='low'
    elif explanation and not _SENSITIVE_MUTATION.search(q):
        level='low'
    elif hits and actionable:
        level='high'
    elif actionable:
        level='medium' if skill['risk_level']=='low' else skill['risk_level']
    else:
        level=skill['risk_level']
    if requested=='strict':level='high'
    elif requested=='light' and level!='high':level='low'
    elif requested=='standard' and level=='low':level='medium'
    return level,{'low':'light','medium':'standard','high':'strict'}[level],hits


def score(task:str, catalog:dict, primary:dict)->list[tuple[int,str,list[str]]]:
    q=normalized(effective_text(task));out={}
    for rule in primary['routes']:
        hits=[t for t in rule['terms'] if normalized(t) in q]
        if hits and rule['id'] in catalog:
            score_value=12+max(len(normalized(t)) for t in hits)
            old=out.get(rule['id'],(0,[]))
            out[rule['id']]=(max(old[0],score_value),hits)
    for i,r in catalog.items():
        if normalized(i) in q:
            out[i]=(100,[i]);continue
        title=normalized(r['name'])
        if len(title)>=3 and title in q:
            old=out.get(i,(0,[]));out[i]=(max(old[0],22),[r['name']])
    # Strong intent patterns override incidental matches to domain nouns.
    if ui_only(task):
        out['frontend.static_page_build']=(120,['presentation-only edit'])
        # Domain-auth/payment workflows are not selected for CSS-only changes.
        for sid in list(out):
            if sid.startswith(('backend.','security.','database.','architecture.auth')):
                del out[sid]
    else:
        for matcher,sid in _SPECIALIZED:
            if matcher.search(task) and sid in catalog:
                out[sid]=(max(out.get(sid,(0,[]))[0],37),[matcher.pattern])
        if re.search(r'(新建|创建|搭建|初始化|create|bootstrap|scaffold).*(next\.?js|前端|react|vue|网站|app)',task,re.I):
            out['frontend.frontend_project_init']=(70,['framework app setup'])
    return sorted(((v[0],k,v[1]) for k,v in out.items()),key=lambda x:(-x[0],x[1]))


def route(task:str,limit:int=3, mode:str|None=None)->dict:
    catalog=load();primary=json.loads(PRIMARY.read_text(encoding='utf-8'))
    rankings=score(task,catalog,primary)
    if not rankings:
        rankings=[(1,'core.project_context_collector',['no match: request project context'])]
    selected=[]
    for s,i,hits in rankings[:max(1,min(limit,5))]:
        r=catalog[i]; risk,chosen,flags=risk_for(task,r,mode)
        selected.append({'id':i,'name':r['name'],'path':r['path'],'base_risk':r['risk_level'],
          'task_risk':risk,'mode':chosen,'match':hits,'score':s,
          'verification_profile':r['verification_profile'],'next_skills':r['next_skills']})
    chosen_mode='strict' if any(s['mode']=='strict' for s in selected) else ('standard' if any(s['mode']=='standard' for s in selected) else 'light')
    return {'task':task,'execution_mode':chosen_mode,'selected':selected,
      'rules':['policies/COMMON.md']+(['policies/HIGH_RISK.md'] if chosen_mode=='strict' else []),
      'note':'Skill recommendation only. Tool execution and production access require separate authorization.'}

def project_dir(p:str)->Path:
    path=Path(p).resolve()
    if path==Path('/') or not path.is_dir(): raise ValueError('project path must be an existing directory')
    return path

def ai_folder(project:Path)->Path: return project/'.ai'

def init(project:Path,force:bool=False)->dict:
    directory=ai_folder(project);directory.mkdir(parents=True,exist_ok=True)
    if directory.resolve()!=project.resolve()/'.ai':raise ValueError('symlink .ai directory is forbidden')
    defaults={
      'project_context.md':'# 项目上下文\n\n- 项目目标：待填写\n- 技术栈：待填写\n- 验收目标：待填写\n',
      'decisions.md':'# 架构决策记录\n\n格式：日期 / 决策 / 备选 / 理由 / 影响\n',
      'known_issues.md':'# 当前已知问题\n',
      'change_history.md':'# 变更记录\n',
      'task_state.json':json.dumps({'schema_version':1,'tasks':[]},ensure_ascii=False,indent=2)+'\n',
      '.gitignore':'# Private local AI work products: may contain source snapshots or diagnostics\nchanges/\nreports/\nproposals/\nloops/\ncache/\ntask_state.lock\n',
      'checks.json':json.dumps({'checks':[{'name':'python-unittest','cwd':'.','args':['python','-m','unittest','discover','-s','tests','-v'],'timeout_seconds':30,'enabled':False}]},ensure_ascii=False,indent=2)+'\n'
    }
    written=[]
    for name,content in defaults.items():
        path=directory/name
        if not path.exists() or force:
            path.write_text(content,encoding='utf-8');written.append(str(path))
    return {'project':str(project),'created':written}

def _read_tasks(project:Path)->tuple[Path,dict]:
    path=ai_folder(project)/'task_state.json'
    if path.is_symlink():raise ValueError('task state symlinks are not accepted')
    data=json.loads(path.read_text('utf-8'))
    if not isinstance(data.get('tasks'),list):raise ValueError('malformed task state')
    return path,data


def _atomic_write(path:Path, data:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.task_',delete=False) as f:
        temp=Path(f.name)
        json.dump(data,f,ensure_ascii=False,indent=2)
        f.write('\n');f.flush();os.fsync(f.fileno())
    try:temp.replace(path)
    finally:temp.unlink(missing_ok=True)


@contextmanager
def _task_lock(project:Path):
    """Serialize task-state updates for concurrent CLI users on the same host."""
    folder=ai_folder(project);folder.mkdir(parents=True,exist_ok=True)
    if folder.resolve()!=project.resolve()/'.ai':raise ValueError('symlink .ai directory is forbidden')
    lockfile=folder/'task_state.lock'
    if lockfile.is_symlink():raise ValueError('symlink lock file is forbidden')
    with lockfile.open('a+b') as handle:
        if os.name=='nt':
            import msvcrt
            handle.seek(0);handle.write(b'0');handle.flush();handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX)
        try:yield
        finally:
            if os.name=='nt':
                handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(handle,fcntl.LOCK_UN)


def status(project:Path)->dict:
    path=ai_folder(project)/'task_state.json'
    if not path.exists():return {'tasks':[],'note':'run init first'}
    _,data=_read_tasks(project)
    # Verify existing report fingerprints without modifying task state.
    for t in data['tasks']:
        for e in t.get('evidence',[]):
            if e.get('verification')!='check_runner':continue
            try:
                f=project/e['path']
                if f.resolve().parent!=(ai_folder(project)/'reports').resolve():
                    raise ValueError('evidence path escapes project reports')
                e['integrity']='valid' if hashlib.sha256(f.read_bytes()).hexdigest()==e['sha256'] else 'modified'
            except (KeyError,OSError,ValueError):e['integrity']='missing_or_invalid'
    return data


def add_task(project:Path,task_id:str,title:str,skill_id:str|None=None)->dict:
    with _task_lock(project):
        directory=ai_folder(project);directory.mkdir(parents=True,exist_ok=True)
        if not (directory/'task_state.json').exists(): init(project)
        path,data=_read_tasks(project)
        if any(t['id']==task_id for t in data['tasks']):raise ValueError('task id already exists')
        if skill_id is not None and skill_id not in load():raise ValueError('unknown skill id')
        t={'id':task_id,'title':title,'status':'todo','skill_id':skill_id,'evidence':[],
           'updated_at':dt.datetime.now(dt.timezone.utc).isoformat()}
        data['tasks'].append(t);_atomic_write(path,data)
        return t


def _verify_report(project:Path, report_name:str)->dict:
    # Evidence must be an actual run_checks-generated report at the fixed reports location.
    reports=(ai_folder(project)/'reports').resolve()
    if reports.parent!=(ai_folder(project)).resolve() or (ai_folder(project)).resolve()!=project.resolve()/'.ai' or (ai_folder(project)/'reports').is_symlink():
        raise ValueError('evidence directory must be inside the project and must not be a symlink')
    evidence=(reports/report_name).resolve()
    if evidence.parent!=reports or not report_name.endswith('.json') or not evidence.is_file():
        raise ValueError('evidence must be a JSON report in .ai/reports/')
    raw=evidence.read_bytes();r=json.loads(raw)
    if r.get('schema_version')!=2 or r.get('project')!=str(project.resolve()) or r.get('actually_executed') is not True:
        raise ValueError('evidence is not an executed report for this project')
    if not r.get('checks') or any(c.get('status')!='passed' for c in r['checks']):
        raise ValueError('evidence checks have not all passed')
    return {'path':str(evidence.relative_to(project)), 'sha256':hashlib.sha256(raw).hexdigest(),
            'created_at':r.get('timestamp'),'checks':[c['name'] for c in r['checks']], 'verification':'check_runner'}


def set_task(project:Path,task_id:str,status:str,checked:bool=False,report:str|None=None,
             manual_reason:str|None=None)->dict:
    with _task_lock(project):
        path,data=_read_tasks(project)
        matches=[t for t in data['tasks'] if t['id']==task_id]
        if not matches:raise ValueError('unknown task id')
        t=matches[0]
        if status=='done':
            if checked:raise ValueError('--verified alone is no longer sufficient; attach --report or --manual-reason')
            if bool(report)==bool(manual_reason):raise ValueError('done requires exactly one of --report or --manual-reason')
            if report: evidence=_verify_report(project,report)
            else:
                if len(manual_reason.strip())<12:raise ValueError('manual verification reason must be at least 12 characters')
                evidence={'verification':'manual_attestation','reason':manual_reason.strip(),
                          'created_at':dt.datetime.now(dt.timezone.utc).isoformat()}
            t.setdefault('evidence',[]).append(evidence)
        elif report or manual_reason or checked:raise ValueError('verification options only apply when status=done')
        t['status']=status;t['updated_at']=dt.datetime.now(dt.timezone.utc).isoformat()
        _atomic_write(path,data)
        return t

def main(argv=None):
    parser=argparse.ArgumentParser(description='AI Fullstack Skills V2 router and task state (no implicit execution)')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('route');p.add_argument('--task',required=True);p.add_argument('--limit',type=int,default=3);p.add_argument('--mode',choices=['light','standard','strict'])
    p=sub.add_parser('init');p.add_argument('--project',default=str(ROOT/'project'));p.add_argument('--force',action='store_true')
    p=sub.add_parser('add-task');p.add_argument('--project',default=str(ROOT/'project'));p.add_argument('--id',required=True);p.add_argument('--title',required=True);p.add_argument('--skill')
    p=sub.add_parser('set-task');p.add_argument('--project',default=str(ROOT/'project'));p.add_argument('--id',required=True);p.add_argument('--status',choices=['todo','in_progress','blocked','done'],required=True);p.add_argument('--verified',action='store_true',help='deprecated: not sufficient to mark done');p.add_argument('--report',help='report filename from .ai/reports');p.add_argument('--manual-reason',help='explicit manual acceptance for non-executable tasks')
    p=sub.add_parser('status');p.add_argument('--project',default=str(ROOT/'project'))
    args=parser.parse_args(argv)
    try:
        if args.command=='route': value=route(args.task,args.limit,args.mode)
        else:
            project=project_dir(args.project)
            if args.command=='init':value=init(project,args.force)
            elif args.command=='add-task':value=add_task(project,args.id,args.title,args.skill)
            elif args.command=='set-task':value=set_task(project,args.id,args.status,args.verified,args.report,args.manual_reason)
            else:
                path=ai_folder(project)/'task_state.json'
                value=status(project)
        print(json.dumps(value,ensure_ascii=False,indent=2))
    except (ValueError,OSError,json.JSONDecodeError) as e:
        parser.exit(2,f'error: {e}\n')
if __name__=='__main__':main()
