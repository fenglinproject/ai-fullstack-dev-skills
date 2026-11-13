# V4.3 Trusted Local Git Repository Validation

This example **creates a fresh temporary Git repository** from the bundled `workflow-demo` source.

```bash
# Preview-only (does not execute source tests)
python examples/v43-repo-demo/run_demo.py

# Explicitly opt in to running trusted bundled Python unit tests in a temp repo
python examples/v43-repo-demo/run_demo.py --execute-tests --rounds 3
```

The executed run performs actual `git init`, branch creation, three reviewed code edits, a unit-test run for each edit, approval-gated commits, one offline PR draft, dashboard projection and read-only repository audit. Up to five rounds are supported. All generated data is discarded with the temporary directory.

The project test runner is **not a sandbox**. Do not swap in untrusted repositories. The demo does not invoke a model, contact a Git remote, publish PRs or deploy anything.
