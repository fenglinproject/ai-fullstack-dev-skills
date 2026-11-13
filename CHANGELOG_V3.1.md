# Changelog — V3.1 (opt-in coding-model connector)

## Added

- `orchestrator/agent.py`: **optional real OpenAI-compatible Chat Completions HTTP integration** using the Python standard library. The user supplies the model, endpoint, API key environment variable and explicit `--send-to-model` consent. No AI credentials are bundled.
- Explicit 1–12-file input allowlist with per-file and total size limits; source hashes; local model response replay; candidate patches validated against the V3 JSON proposal format and current hashes before saving.
- On `init`, create `.ai/.gitignore` for proposals, recovery manifests, local reports and lock files. Proposals are saved under `.ai/proposals/`. Sending source to the model never directly edits project files; `workflow.py preview` and human `apply --approve` remain separate required steps.
- Diagnostic mode: accept a **failed, actually executed** `.ai/reports/checks-*.json` test report, include bounded failure snippets in the model request, and request a new reviewable repair proposal. No automatic apply or unlimited repair attempts.
- `orchestrator/git_review.py`: bounded, read-only Git file status / diffs / `diff --check` for a V3 change ID. Never stages, commits, pushes or runs Git hooks.
- `tests/test_agent_bridge.py`: offline end-to-end test, local HTTP protocol integration test, source privacy restrictions, invalid output rejection, report validation and Git review checks.
- New instructions in `START_HERE.md`, `docs/AGENT_INTEGRATION.md`, and `SECURITY.md`.

## Preserved

- All 144 specialist Skills and 30 primary skill entries; V3.0 human approval, separate high-risk attestation, hash-pinned edits, rollback and task verification.
- V2.1 routing, catalog auditing and runnable Todo API example.

## Limitations / threat model

- The local HTTP test uses a **mock model service**, not a paid external provider. The live HTTP client is implemented, but actual third-party provider calls require the user's credentials and compatible endpoint.
- The selected sources, task text and optional failed-test diagnostics go to the endpoint explicitly named by the operator. Review this data before opting in; redaction heuristics cannot guarantee that all secrets are detected.
- No autonomous agent with tool-calling or repository-wide indexing, automatic application, automatic test execution, Git commits, PR creation, deployment or model-based self-repair without human review.
- Test execution remains opt-in and is NOT sandboxed; run only trusted project tests in a suitable isolated environment when necessary.
- Local proposal, task and backup files are editable records, not cryptographic attestations.
