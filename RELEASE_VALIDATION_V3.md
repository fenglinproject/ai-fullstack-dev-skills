# V3.0 Release Validation — 2026-11-05

Tests executed locally against the extracted V2.1 base with V3.0 additions, using
Python 3.13. GitHub Actions uses Python 3.11; CI execution on a remote runner is
**not** claimed here.

| Check | Local outcome |
|---|---|
| `python -m unittest discover -s tests -q` | **PASS**, 73 tests |
| `python tools/benchmark_router.py` | **PASS**, skill 28/28 and mode 28/28 |
| `python tools/sync_catalog.py --check` | **PASS**, catalog current |
| `python tools/audit_catalog.py` | **PASS**, 144 skills, 30 primary entries, zero issues and warnings |
| `cd examples/runnable-todo && python -m unittest discover -s tests -q` | **PASS**, 11 API tests |
| `python -m compileall -q orchestrator tools tests examples/workflow-demo/src examples/workflow-demo/tests` | **PASS** |
| `tests/test_workflow_demo.py` copied example: preview → approve → verify → done → restore → blocked | **PASS**, included in 73 tests |
| Independent CLI round trip in a temporary directory (preview, apply, review, verify, status, restore, status) | **PASS**, 1 test executed; task transitioned done → blocked on restore |

The V3 suite includes direct tests for denied path traversal, symlinks, unsafe files,
stale hashes, conflicting edits, double-approval for sensitive paths, unapproved
modifications, rollback protection, and evidence handling. These checks do not prove
complete sandbox isolation or security for untrusted source. The 28 routing cases
are fixed in-repository examples, not independent real-world accuracy metrics.

## Capability boundary

- No built-in AI agent or automatic debugging/retry loop; external coding assistants
  may generate a proposal but are NOT invoked by these commands.
- Multi-file local text operations are best-effort and recoverable, not a filesystem
  transaction. Only replace/create actions are supported.
- Read-only Git metadata included; no commit, branch, pull request, or deployment.
- Tests can execute arbitrary code from a **trusted** project; the runner is not a sandbox.
- Verification fingerprints the files changed by the proposal, **not the entire repo**.
- Run-time review gates are human attestation flags and cannot replace access controls.
