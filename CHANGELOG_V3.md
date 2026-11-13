# Changelog — V3.0

## Added

- `orchestrator/workflow.py`: local proposal protocol, deterministic preflight,
  unified diff preview, explicit approval-gated edits, backup manifest, drift review,
  opt-in trusted-check execution and conditional task completion, controlled rollback.
- Separate `--high-risk-reviewed` attestation for strict-risk tasks and sensitive file paths.
- `handoff` output for external coding assistants to request source inspection and a
  JSON proposal without granting the library implicit code-generation capabilities.
- `docs/agent_proposal.schema.json`: documented JSON proposal contract.
- `docs/AGENT_INTEGRATION.md`: integration boundaries, review workflow and limitations.
- `examples/workflow-demo/`: deliberately failing test fixed by a reviewed proposal.
- `tests/test_workflow.py`: happy-path and adversarial tests, including path traversal,
  symlinks, stale source, post-apply drift, rejection of unapproved operations and rollback.

## Preserved

- All 144 specialist Skills and 30 primary route entries.
- V2.1 router, task state, hash-linked verification reports, read-only impact scan,
  catalog consistency checks, runnable Todo example and standard unit tests.

## Security limitations

- No default permission to run any AI model, shell command, install packages, commit,
  deploy, make network requests, or run tests against untrusted code.
- `.ai/changes` contains plaintext backup snapshots of modified text files; it is
  ignored by Git but still needs local access protection.
- The check runner remains **not a sandbox**; tests can execute arbitrary repository code.
- The code workflow supports create/replace text edits only, not deletion, renames,
  database migration, package installation, or multi-agent autonomous repair.
- Git data are read-only and optional. No Git commit or pull request is produced.
