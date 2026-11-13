# V3.1 coding-model integration and review-first workflow

The library now includes an **opt-in model client** (`orchestrator/agent.py`) for
OpenAI-compatible **Chat Completions** endpoints. It uses the Python standard
library and has no mandatory third-party package dependencies.

## 1. Select sources and inspect the context without calling a model

```bash
python orchestrator/cli.py init --project examples/workflow-demo
python orchestrator/agent.py context --project examples/workflow-demo \
  --task-id DEMO-1 --task "Fix greeting punctuation in example code" \
  --include src/formatter.py
```

The command shows the files and SHA-256 hashes that *would* be sent. Open and
review each source file before sharing it. Only explicitly included UTF-8 paths
are sent (up to 12 files, max 32 KiB per file / 128 KiB total); private keys
and several known credential formats trigger a best-effort rejection. Not all
sensitive information can be detected automatically. Skill excerpts selected
by the local router are also included in the model request.

## 2A. No API key? Replay an offline model response

```bash
python orchestrator/agent.py propose --project examples/workflow-demo \
  --task-id DEMO-1 --task "Fix greeting punctuation in example code" \
  --include src/formatter.py \
  --response-file examples/workflow-demo/proposal.json
```

This verifies the **proposal generation interface**, schema compatibility, path
and hash restrictions without contacting any service. The response file is a
pre-written example, not proof that a real model created it.

## 2B. Connect a compatible endpoint with explicit source-sharing consent

Set a credential in the environment, **never** in code or command arguments:

```bash
export AI_CODING_API_KEY="YOUR_KEY_FROM_PROVIDER"
python orchestrator/agent.py propose --project path/to/your/project \
  --task-id TASK-1 --task "Improve the selected module and keep behavior compatible" \
  --include src/module.py \
  --endpoint 'https://YOUR_PROVIDER/v1/chat/completions' \
  --model 'YOUR_COMPATIBLE_MODEL' \
  --send-to-model
```

PowerShell environment setup: `$env:AI_CODING_API_KEY = "YOUR_KEY_FROM_PROVIDER"`.

This sends the selected file text, hashes, task description, chosen Skill
excerpts and optional failed-test diagnostics to the operator-supplied provider.
By default only HTTPS endpoints are allowed. For **loopback local model gateways
only**, add `--allow-local-http` with an `http://127.0.0.1:PORT/...` endpoint.
HTTP redirects are disabled. The model API must support a standard
Chat Completions `messages` request and a text `choices[0].message.content`
response. Some providers/models use different request fields; these may need
provider-specific adapters in a future release. No API token is written to disk.

To authorize a **new file**, explicitly include one or more relative destination
folders using `--allow-create-prefix src/new_module` (or the precise directory
required). Without this flag, the model may replace only explicitly included
files; it may not create files. File deletion is unsupported.

## 3. Inspect and approve the generated proposal

The agent returns a path such as `.ai/proposals/agent-<id>.json`. Replace
`PROPOSAL_PATH` below with that exact path from the output:

```bash
python orchestrator/workflow.py preview --project YOUR_PROJECT --proposal PROPOSAL_PATH
python orchestrator/workflow.py apply --project YOUR_PROJECT --proposal PROPOSAL_PATH --approve
```

Inspect **every unified diff** before applying. Sensitive paths/tasks require
additional `--high-risk-reviewed`. A model response is **never** an approval.
V3 checks source hashes again at application time and protects against stale
source changes. A proposal may contain insecure code even if it is structurally
valid, so code review is essential.

## 4. Verify, diagnose failures, and propose a repair

```bash
python orchestrator/workflow.py verify --project YOUR_PROJECT --change-id CHANGE_ID --run
```

`--run` executes the explicitly enabled local test commands; inspect and trust
the test code first. The resulting report path is under `.ai/reports/`.
For failing checks, request **another** proposal:

```bash
python orchestrator/agent.py propose --project YOUR_PROJECT \
  --task-id FIX-2 --task "Fix the test failure in the selected module" \
  --include src/module.py --report checks-REPORT_ID.json \
  --endpoint 'https://YOUR_PROVIDER/v1/chat/completions' \
  --model 'YOUR_COMPATIBLE_MODEL' --send-to-model
```

This transmits a bounded failed-test excerpt in addition to the sources. Every
repair proposal requires a **new** diff review and approval. Do not run
untrusted tests on your personal computer: the test runner is not a sandbox.

For a verified change in its own Git repository, review only:

```bash
python orchestrator/git_review.py --project YOUR_PROJECT --change-id CHANGE_ID
```

It returns tracked-file diffs, untracked statuses and whitespace warnings. It
**does not** stage, commit, push, open a PR or include untracked file contents
in the Git diff; these actions remain part of normal project-specific review.

## 5. Remaining limits

- No fully autonomous tool-calling agent, iterative self-repair loop, or
  repository-wide semantic indexing.
- No automatic Git commit or production deployment.
- Model content may be wrong or malicious: the human approval and V3 checks
  must not be bypassed. Local Git, evidence and backups are convenience records.
- Explicit execution remains restricted to the V3 trusted-check runner;
  provider access does not grant shell access.
