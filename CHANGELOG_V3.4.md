# Changelog — V3.4

## Added

- `tools/semantic_impact.py`: read-only Git HEAD versus working-tree Python AST symbol hints, explicit import candidates and transitive import impact. Incomplete semantics explicitly labeled.
- `orchestrator/github_ci.py`: opt-in GitHub CLI integration; offline preview, remote PR CI inspection, explicitly authorized draft PR creation after local reviewed commit and passing evidence. No implicit push/merge/deploy.
- `tools/loop_metrics.py`: private-text-free aggregate of local capped repair journals, including success/failure rounds and elapsed time.
- `tests/test_v34.py`: new regression tests for all three capabilities, including mocked remote GitHub responses and failure boundaries.
- `.github/pull_request_template.md`: reviewer checklist with independent CI and security gates.
- `.github/workflows/test.yml`: manual dispatch and short-retention audit/benchmark artifacts.
- `docs/ENGINEERING_V3.4.md`: usage, prerequisites, caveats, permission boundaries.

## Existing behavior retained

- All 144 professional skills and V3.3 tools, approval, tests, local Git operations, loop state and rollback mechanics.
- No unattended source modification, remote push, PR merge or production deployment.

## Known limits

- GitHub CLI remote access is opt-in and requires a separately configured gh session; tests use a mocked service.
- Code impact does not implement complete language-server semantics or dynamic interprocedural dataflow.
- Loop metrics rely on saved local evidence, not independently measured success.
- Docker end-to-end security claims remain out of scope until run and reviewed in a Docker-equipped environment.
