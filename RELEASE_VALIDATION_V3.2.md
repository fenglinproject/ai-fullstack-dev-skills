# V3.2 Release Validation

Date: 2026-11-05

## Tests performed on this release candidate

| Check | Result |
|---|---|
| Skill catalog consistency: `python tools/sync_catalog.py --check` | Passed |
| Directory and reference audit: `python tools/audit_catalog.py` | Passed, 144 skills, 30 primary entries, zero audit errors |
| Router benchmark: `python tools/benchmark_router.py` | 28/28 skill selections and 28/28 mode selections |
| Python source compilation: `python -m compileall -q orchestrator tools tests examples/loop-demo examples/runnable-todo/backend` | Passed |
| Full orchestrator/tool suite: `python -m unittest discover -s tests -v` | **106/106** passed |
| Runnable Todo API example: `(cd examples/runnable-todo && python -m unittest discover -s tests -q)` | **11/11** passed |
| Two-round offline demo: `python examples/loop-demo/run_offline_demo.py` | First round failed as expected, second round passed, reverse rollback restored original |

## Key scenarios in the 106 tests

- Offline proposal generation does not edit source; explicit approval is needed.
- Test invocation requires independent `--trust-project-code` attestation.
- A failed executed test may trigger a new repair proposal only when remaining
  rounds exist and corresponding report/source hashes match.
- A successful later round closes the task with a real test report.
- Abort with rollback restores two applied changes in reverse order.
- Drift, tampered proposal/report, stale hashes and over-limit iterations halt.
- Recovery finds an applied operation when interruption happened between source
  apply and session journal update; in-flight tests do not automatically re-run.
- CLI subprocess contract validates two rounds, progress inspection and rollback.

## Important limitations

The tested repair proposals use local offline model-response files. V3.1 HTTP
integration tests use local mock endpoints; no live external model credentials
were present or used. All local unit tests run **trusted project code**; the
runner is not a hardened sandbox. Assertions about security and correctness are
limited to the executed fixtures and tracked behavior, not production readiness.
