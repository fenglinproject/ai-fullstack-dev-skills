# AI Fullstack Dev Skills V3.4 — Release validation

Validated on 2026-11-06 using Python 3.13.5, local POSIX filesystem, and Git. This record covers local execution only.

| Test | Command / scope | Observed result |
|---|---|---|
| Skill index consistency | `python tools/sync_catalog.py --check` | Passed |
| Catalog integrity | `python tools/audit_catalog.py` | Passed, 144 Skill entries, no issues or warnings |
| Python syntax | `python -m compileall -q orchestrator tools tests examples/runnable-todo/backend examples/loop-demo` | Passed |
| Tools and workflow regression | `python -m unittest discover -s tests -q` | **141/141 passed**; includes 20 new V3.4 cases |
| Router golden tasks | `python tools/benchmark_router.py` | **28/28 skill top-1 and 28/28 execution modes** |
| Example API regression | `(cd examples/runnable-todo && python -m unittest discover -s tests -q)` | **11/11 passed** |
| CI workflow syntax | PyYAML parsed `.github/workflows/test.yml` | Parsed successfully |
| Git integration | V3.4 tests use temporary initialized Git repositories and committed fixtures | Passed local branch, commit, baseline impact and PR preflight checks |
| GitHub API/CLI | Read-only check responses and draft publication **mocked** | Validation of command construction, explicit approval and URL filtering passed; **no live GitHub request** |
| Docker isolated runner | Not installed in this environment | No real container execution; V3.3 container adapter remains unverified on Docker |

## Added/changed

- `orchestrator/github_ci.py` for explicitly opt-in GitHub CI inspection and draft PR publication.
- `tools/semantic_impact.py` for Git baseline Python public symbol/import hints.
- `tools/loop_metrics.py` for aggregated repair-session metrics without task/source content.
- `.github/workflows/test.yml` manual dispatch and upload of bounded audit/benchmark artifacts.
- `.github/pull_request_template.md` maintainer checklist, V3.4 docs, CLI entrypoints.
- `tests/test_v34.py` (20 cases).

## Claims and boundaries

All tests here are local. No third-party LLM, Docker daemon or live GitHub repo were contacted. GitHub Draft PR creation requires an available authenticated GitHub CLI plus explicit `--execute --approve` and an already manually pushed branch. No Git push, merge, production deployment or autonomous cloud CI setup occurs in this release. Python symbol scanning is a heuristic, not complete semantic code analysis. Repair metrics reflect stored session status, not independently verified productivity gains. CI configuration only becomes an online run when installed in a GitHub repository with Actions enabled.
