# V3.2: Bounded development/repair sessions

V3.2 connects V3.1's explicit source snapshot, model-backed proposals, V3 apply,
and trusted test runner into a **bounded state machine**. It is not an unattended
autonomous coding agent. A proposal **never** automatically writes source, and
proposals are not auto-approved. Each test execution requires a separate flag.

## Quick start (offline model response)

Use your own **trusted** existing project with `.ai/` initialized, a vetted and
enabled `.ai/checks.json`, and an offline response containing a valid V3 proposal
for exactly the source file(s) you select.

```bash
python orchestrator/cli.py init --project /path/to/project
python orchestrator/loop.py start --project /path/to/project \
  --task "Fix greeting punctuation in the demo module" --task-id TASK-32 \
  --include src/formatter.py --max-rounds 3 --response-file /path/to/response.json
# Copy the run_id from the JSON response and inspect the .ai/proposals file.
python orchestrator/loop.py status --project /path/to/project --run-id RUN_ID
python orchestrator/loop.py approve --project /path/to/project --run-id RUN_ID --approve
# Only run tests when you trust the project/test code; this is NOT sandboxed.
python orchestrator/loop.py test --project /path/to/project --run-id RUN_ID --trust-project-code
# If status is awaiting_repair, obtain a repair proposal using the failed report:
python orchestrator/loop.py repair --project /path/to/project --run-id RUN_ID \
  --response-file /path/to/repair_response.json
# Review the NEW proposal then repeat approve and test. Round count is capped.
```

To request a remote model for `start` or `repair`, supply `--endpoint`, `--model`,
`--send-to-model`, and an API key using `--api-key-env` (default
`AI_CODING_API_KEY`). If sending source is disallowed, keep using offline files.
The model sees only the explicitly included sources and, during repair, a bounded
excerpt of the failed test report. Review all material before opting into network
transmission. Credential-like content is screened but no detector is exhaustive.
No API key is persisted in loop state.

## State transitions

```text
start --> awaiting_approval --approve--> awaiting_test --trust-project-code--> completed
                                                  |                  |
                                                  | test failure     | test plan not verified
                                                  v                  v
                                           awaiting_repair        unverified
                                                  |
                                       repair (rounds < cap)
                                                  v
                                           awaiting_approval

When the last allowed round fails --> exhausted
Any stable stage --> abort [optionally --restore --approve] --> aborted
Interrupted apply --> status/resume reconciles via operation_id
Interrupted tests --> testing; explicit re-run required
```

`status` and `resume` inspect the persisted `.ai/loops/RUN_ID/state.json` journal;
these commands **never automatically execute code**. If a process stops between
applying source and updating the journal, an operation marker in the persisted
V3 change manifest allows `resume` to recover the applied `change_id`. An
incomplete/ambiguous apply is marked `recovery_needed`; inspect the files and
backup manifests manually, do not automatically overwrite the tree.

At `max_rounds` (1–5; default 3), the workflow stops instead of retrying forever.
`unverified` means no checks actually failed but the suite was not all passing
(e.g. all checks disabled), so it does not hallucinate a repair diagnosis.

## Safe stop, cancel and rollback

```bash
python orchestrator/loop.py abort --project /path/to/project --run-id RUN_ID
# This stops the loop but leaves approved source edits in place.
python orchestrator/loop.py abort --project /path/to/project \
  --run-id RUN_ID --restore --approve
# Restores applied edits in reverse order, only while hashes match.
```

If rollback detects newer edits, it refuses to overwrite them and records
`rollback_blocked`. A restore also downgrades an already-completed task to
`blocked`. No `git reset`, checkout, commit, push or production deployment occurs.

## Security and engineering limitations

- Model output is **untrusted data**; existing V3 preflight, hash pinning and
  approvals remain mandatory. Each subsequent repair is based on the *current*
  source snapshot, not the original pre-change text.
- Test scripts execute arbitrary project code. The allowlisted test command is
  **not an execution sandbox**, and the demo must not be generalized to untrusted
  repositories. For untrusted code, use separately provisioned isolation.
- Neither true zero-touch autonomous iteration nor Git PR creation, parallel
  agents, universal dependency analysis, deployments, or production safety are
  implied. Human approval is intentionally part of each iteration.
- Network model calls are opt-in per round and are **not validated against a
  paid live external model** unless you configure credentials and call one.
- `start`/`repair` can use offline JSON model responses. The repository's tests
  cover the model interface through mocks, not a guaranteed provider SLA.
- The `.ai` folder may include full source backups, model output and log tails;
  it must stay private, access controlled, and Git-ignored.
