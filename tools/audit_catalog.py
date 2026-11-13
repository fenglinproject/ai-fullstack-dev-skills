#!/usr/bin/env python3
"""Catalog structural audit with machine-readable result and human report."""
import collections
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VALID_RISK={'low','medium','high'}
VALID_MODE={'light_or_standard','standard','strict'}

def audit():
    data=json.loads((ROOT/'skill_routing_matrix.json').read_text('utf-8'))
    ids={r['id'] for r in data}
    paths=set();issues=[];warnings=[]
    if len(ids)!=len(data):issues.append('duplicate skill IDs')
    for r in data:
        i=r['id']; path=r['path']
        if not path.startswith('skills/') or '..' in Path(path).parts:issues.append(f'{i}: invalid path')
        if not (ROOT/path).is_file():issues.append(f'{i}: missing file {path}')
        if path in paths:issues.append(f'{i}: path reused')
        paths.add(path)
        if r.get('risk_level') not in VALID_RISK:issues.append(f'{i}: invalid risk')
        if r.get('execution_mode') not in VALID_MODE:issues.append(f'{i}: invalid mode')
        if r.get('risk_level')=='high' and r.get('execution_mode')!='strict':issues.append(f'{i}: high risk is not strict')
        for nxt in r.get('next_skills',[]):
            if nxt not in ids:issues.append(f'{i}: unresolved next_skills {nxt}')
            if nxt==i:issues.append(f'{i}: self-referential next_skill')
        for ref in r.get('policy_refs',[]):
            if not (ROOT/ref).is_file():issues.append(f'{i}: missing policy {ref}')
        text=(ROOT/path).read_text('utf-8') if (ROOT/path).exists() else ''
        if len(text)<200:warnings.append(f'{i}: very short skill')
        if '<!-- routing_matrix_enhancement_v1 -->' in text:issues.append(f'{i}: old boilerplate not removed')
    actual=set(str(p.relative_to(ROOT)) for p in (ROOT/'skills').rglob('SKILL.md'))
    if actual!=paths:issues.append(f'catalog/files mismatch: extra files {sorted(actual-paths)[:10]}')
    primary=json.loads((ROOT/'orchestrator/primary_skills.json').read_text('utf-8'))
    for i in primary['primary']:
        if i not in ids:issues.append(f'primary missing: {i}')
    for item in primary['routes']:
        if item['id'] not in ids:issues.append(f'route target missing: {item["id"]}')
    # Legacy index must match the routing matrix, not contain stale V1 dependencies.
    try:
        from tools.sync_catalog import build_index
    except ModuleNotFoundError:
        from sync_catalog import build_index
    actual_index=json.loads((ROOT/'skills_index.json').read_text('utf-8'))
    if actual_index!=build_index():issues.append('skills_index.json differs from canonical routing data: run python tools/sync_catalog.py')
    for skill in actual_index.get('skills',[]):
        for nxt in skill.get('next_skills',[]):
            if nxt not in ids:issues.append(f'index: unresolved next_skill {nxt}')
    count=collections.Counter(r['risk_level'] for r in data)
    return {'skills':len(data),'stage_count':len(set(r['stage'] for r in data)), 'risk_counts':dict(count),
            'primary_count':len(primary['primary']),'issues':issues,'warnings':warnings,'passed':not issues}

def main():
    result=audit()
    md=['# V2 Skill 目录与质量审计','',f'- 技能数：{result["skills"]}',
        f'- 阶段数：{result["stage_count"]}',f'- 主入口数：{result["primary_count"]}',
        f'- 基础风险：{result["risk_counts"]}',f'- 结构审核：{"PASS" if result["passed"] else "FAIL"}',
        '', '## 错误', '']
    md+=['- '+issue for issue in result['issues']] or ['- 无']
    md+=['','## 提示','']
    md+=['- '+warning for warning in result['warnings']] or ['- 无']
    md+=['','> 此工具验证目录与引用完整性，不等同于 Skill 实际开发成功率；实际质量须使用基准任务与项目测试评估。']
    (ROOT/'SKILL_QUALITY_REPORT.md').write_text('\n'.join(md)+'\n','utf-8')
    (ROOT/'tools'/'catalog_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
