#!/usr/bin/env python3
"""Create the legacy-compatible skills_index.json from the authoritative routing matrix.

Do not hand-edit skills_index.json. Ids, risks, next skills and verification
commands are taken from skill_routing_matrix.json on every run.
"""
from pathlib import Path
import json
import argparse
ROOT=Path(__file__).resolve().parents[1]
ROUTES=ROOT/'skill_routing_matrix.json'
INDEX=ROOT/'skills_index.json'


def build_index()->dict:
    source=json.loads(ROUTES.read_text('utf-8'))
    old=json.loads(INDEX.read_text('utf-8')) if INDEX.exists() else {}
    by_id={r['id'] for r in source}
    if len(by_id)!=len(source):raise ValueError('duplicate ids in authoritative catalog')
    skills=[]
    for r in source:
        skill={
            'id':r['legacy_id'], 'route_id':r['id'],'name':r['name'],'path':r['path'],
            'category_id':Path(r['path']).parts[1],'category_name':r.get('stage_name'),
            'triggers':r.get('triggers',[]),'inputs':r.get('requires',[]),
            'outputs':r.get('outputs',[]),'depends_on':[],
            'stage':r['stage'],'stage_name':r['stage_name'],'stage_order':r['stage_order'],
            'risk_level':r['risk_level'],'execution_mode':r['execution_mode'],
            'requires':r.get('requires',[]),'next_skills':r.get('next_skills',[]),
            'must_not_do':r.get('must_not_do',[]),
            'tool_adaptation':r.get('tool_adaptation',{}),
            'verification_commands':r.get('verification_commands',[]),
        }
        skills.append(skill)
    return {
        'project_name':old.get('project_name','AI Fullstack Dev Skills'),
        'version':'2.1-generated-from-routing-matrix',
        'description':'兼容索引，由 skill_routing_matrix.json 自动生成；禁止手工编辑。',
        'rules':{
            'execution_modes':{'light':'样式/文案等低风险修改','standard':'常规开发和架构任务',
                               'strict':'实际修改支付、认证、生产环境或数据库结构等高风险操作'},
            'skill_routing':'以 skill_routing_matrix.json 为唯一事实来源；CLI 按任务影响范围选择模式。',
            'verification':'仅已运行并通过的检查可作为自动测试证据；非代码任务可记录明确的人工验收理由。',
            'project_workspace':'项目业务代码存放在 project/ 或独立工作仓库，技能仅提供开发规范。',
        },
        'categories':old.get('categories',[]),
        'skills':skills,
        'important_files':old.get('important_files',{}),
        'routing_matrix':source,
    }


def generate():
    data=build_index()
    INDEX.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true',help='fail if generated index differs')
    a=p.parse_args()
    if a.check:
        if not INDEX.exists() or json.loads(INDEX.read_text('utf-8'))!=build_index():
            p.exit(1,'Stale index: run python tools/sync_catalog.py\n')
        print('Catalog index up to date')
    else:print('Synchronized skills_index.json:',len(generate()['skills']),'skills')
