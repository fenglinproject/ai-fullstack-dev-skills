"""Fixture-only explicit test authorization; not a project default."""
import json
from pathlib import Path

def enable_test_checks(project:Path):
    path=project/'.ai/checks.json'
    data=json.loads(path.read_text('utf-8'))
    for check in data['checks']:
        if check['name']=='python-unittest':check['enabled']=True
    path.write_text(json.dumps(data),encoding='utf-8')
