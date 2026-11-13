# V3.2 — Bounded Human-Gated AI Repair Sessions

Release: 2026-11-05

## New capabilities

- `orchestrator/loop.py`: persistent multi-round development and repair sessions.
  - `start`: select 1–12 source files, request an offline or opt-in remote AI
    proposal, save a reviewable artifact without changing project source.
  - `approve`: inspect proposal separately; explicit approval and V3 hash-pinned
    apply, including high-risk extra acknowledgement where applicable.
  - `test`: explicit opt-in to execute trusted local tests; save test evidence;
    close the task on success, or queue a subsequent repair on test failure.
  - `repair`: give the latest validated failed report to the model/provider,
    and create a *new* reviewable, hash-pinned source proposal.
  - `status`/`resume`: inspect the persistent session, reconstruct applied
    operations after interrupted writes, without automatically running code.
  - `abort`: stop without rollback, or restore approved changes in reverse order
    with an extra approval and refusal to overwrite user changes.
  - `max_rounds`: default 3, maximum 5, with terminal exhausted state and no
    infinite retry loop.
- Journals under `.ai/loops/RUN_ID/state.json` are atomically written and guarded
  by per-run cross-process file locks. Source apply operations carry recovery IDs
  in the existing V3 manifests.
- `unverified` stage distinguishes disabled/unexecuted checks from actual test
  failure; no fake repair evidence is generated.
- Validate report SHA-256 and workflow change association before continuing;
  refusal on stale source, tampered proposal and changed test report.
- Added standalone offline demonstration under `examples/loop-demo/` and the
  detailed manual `docs/LOOP_V3.2.md`.
- Extended root and initialized project Git ignore rules to cover `.ai/loops/`.
- Added unit, CLI, approval-boundary, crash-recovery and two-round integration
  tests. Existing 144 Skill assets and compatibility with V3.1 tools preserved.

## Deliberate boundaries

- **No unattended code mutation**: every round requires independent operator
  approval. Test execution also needs an explicit trusted-project assertion.
- **No real untrusted-code isolation**: `python -m unittest` can run arbitrary
  project code. Use an external sandbox/VM where required.
- No actual remote paid model was called by the release verification. HTTP
  compatibility is tested through local mock services; offline JSON responses
  drive deterministic integration tests.
- No automated Git commit/push/PR, model-controlled shell, dependency install,
  production database action or deployment.
- Local reports/journals are not cryptographically signed and should not be
  mistaken for tamper-proof external attestation.
