# V2.1 Release Validation

Validated locally on 2026-11-05 in a Python 3.13 environment; GitHub Actions pins Python 3.11.

| Check | Result |
|---|---|
| `python tools/sync_catalog.py --check` | PASS; generated index matches canonical routing data |
| `python tools/audit_catalog.py` | PASS; 144 Skills, zero broken references |
| `python -m unittest discover -s tests -q` | PASS; 51 tests |
| `python tools/benchmark_router.py` | PASS; top skill 28/28, risk mode 28/28 |
| `cd examples/runnable-todo && python -m unittest discover -s tests -q` | PASS; 11 API tests |
| `python -m compileall -q orchestrator tools tests examples/runnable-todo/backend` | PASS |
| API test report -> mark task done -> status integrity | PASS; executed report accepted, integrity valid |

All validations apply to code in this package, not arbitrary future projects. The
28 routing cases are fixed, curated prompts; they are not an independent external
benchmark. Source tests in a trusted checkout may perform arbitrary operations.
