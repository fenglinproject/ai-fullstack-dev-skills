# AI Fullstack Dev Skills V2.1 — hardening release

This release builds on V2.0 while preserving all 144 original Skill files.

## Implemented

1. **Intent-aware deterministic routing:** presentation-only CSS changes in login/checkout pages are now routed to frontend skills instead of authentication/payment backends. Negative scope instructions ("do not change database") no longer automatically raise risk. Added Next.js, WeChat Mini Program and Kubernetes intent hints. High-risk production database structure mutations remain strict. This is a rules-based heuristic router, **not** semantic LLM reasoning.
2. **Restricted check runner:** removed arbitrary `npm run`, arbitrary `python -m`, `node -e` and generic shell command support. Narrow allowlist: `python -m unittest discover -s DIR [options]` and `node --check FILE`. Dry-run is default; `--run` explicitly executes *trusted repository code only*. Execution does not sandbox tests; see `SECURITY.md`.
3. **Test evidence:** `--save-report` writes a uniquely named JSON record in `project/.ai/reports/`. Closing a task requires a successful executed report (`--report checks-….json`) or an explicit, sufficiently detailed human attestation (`--manual-reason`). A plain `--verified` no longer suffices. Attached report contents are hashed in task state and rechecked on `status`; locally stored evidence is **not** tamper-proof. Task state updates use a local file lock and atomic replace.
4. **Single catalog source:** `skill_routing_matrix.json` is authoritative; `tools/sync_catalog.py` regenerates `skills_index.json` in a legacy-compatible shape. Removed stale `testing.integration_test` references and added index consistency checking.
5. **Impact references:** `tools/impact_scan.py` searches textual references across code and test files before a rename. It is read-only and does not infer actual semantic dependencies.
6. **Repository hygiene and CI:** added `.gitignore`, `SECURITY.md`, stricter unit/regression tests, catalog consistency step and Python parsing validation.

## Verified locally

- 144/144 Skill entries present and 0 broken catalog references.
- 28/28 original routing golden cases matched the expected top skill and execution mode.
- 51 orchestrator/security/impact/state tests passed.
- 11 runnable Todo API tests passed.

## Not implemented / not claimed

- No secure OS-level sandbox or isolated production executor.
- No LLM or external coding-agent connection and no arbitrary code modification agent.
- No full language-server dependency graph, Git transaction review, code repair agent, or production CI deployment.
- Does not certify third-party dependencies or production readiness of the demo.
