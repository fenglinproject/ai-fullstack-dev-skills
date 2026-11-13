# Release validation — V3.1

Validation in the local Python environment, performed on 2026-11-05.
These figures describe the contents of this artifact; they are not production SLAs.

| Check | Result |
|---|---|
| `python tools/sync_catalog.py --check` | Passed; catalog current |
| `python tools/audit_catalog.py` | Passed; 144 Skills, 30 primary entries, 16 stages; 0 issues / 0 warnings |
| `python -m unittest discover -s tests -q` | Passed; 90 tests |
| `python tools/benchmark_router.py` | Skill 28/28; mode 28/28 |
| `cd examples/runnable-todo && python -m unittest discover -s tests -q` | Passed; 11 API tests |
| `python -m compileall -q orchestrator tools tests examples/runnable-todo/backend` | Passed |
| Local model protocol (in test suite) | Passed: HTTP Chat Completions request / JSON response with explicit opt-in |
| Provider redirect safety (in test suite) | Passed: redirected API requests rejected |
| Offline CLI walkthrough (temp project) | Context read, proposal save, unapproved preview, approved apply, actual passing tests, read-only Git review, approved rollback all passed |

## Executed offline walkthrough

Used a fresh temporary copy of `examples/workflow-demo` and the pre-authored
`proposal.json` model-response fixture, with these commands:

1. `orchestrator/cli.py init --project TEMP_PROJECT`
2. `orchestrator/agent.py context ... --include src/formatter.py`
3. `orchestrator/agent.py propose ... --response-file examples/workflow-demo/proposal.json`
4. `orchestrator/workflow.py preview ...` (no approval)
5. `orchestrator/workflow.py apply ... --approve`
6. `orchestrator/workflow.py verify ... --run --close-task`
7. `orchestrator/git_review.py ... --change-id ...`
8. `orchestrator/workflow.py restore ... --approve`

Observed `all_passed=true` on executed tests, a saved test report, an available
read-only Git review, and successfully restored source files.

## Important limits

- **No real third-party paid LLM API invocation occurred.** A local HTTP mock
  verified request and response protocol, while an offline fixture verified
  proposal validation and application. Provider-specific compatibility and
  service reliability remain to be tested with user-supplied credentials.
- This release does not execute autonomous model tool calls or iterative repair
  loops without review; it does not stage, commit, push or deploy code.
- The check runner executes trusted repository code and is **not** a sandbox.
- A static scanner cannot detect every kind of secret in model input.
