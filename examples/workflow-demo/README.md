# V3 change workflow demonstration

This project starts intentionally **failing** one unit test. The provided proposal corrects the
punctuation, but only after review and explicit human approval. Run the example in a copy of
this folder; `--run` executes local Python test code and is for **trusted** projects only.

From the repository root (use an absolute path or change accordingly):

```bash
python orchestrator/cli.py init --project examples/workflow-demo
python orchestrator/workflow.py preview --project examples/workflow-demo --proposal examples/workflow-demo/proposal.json
python orchestrator/workflow.py apply --project examples/workflow-demo --proposal examples/workflow-demo/proposal.json --approve
# Note the change_id from apply output; replace CHANGE_ID in the next command.
python orchestrator/workflow.py review --project examples/workflow-demo --change-id CHANGE_ID
python orchestrator/workflow.py verify --project examples/workflow-demo --change-id CHANGE_ID --run --close-task
```

An authorized rollback is available with:

```bash
python orchestrator/workflow.py restore --project examples/workflow-demo --change-id CHANGE_ID --approve
```

A restore refuses to overwrite files edited since the recorded apply. It does not use
`git reset`, `git checkout`, delete branches, or touch unrelated files. The demonstration
contains no package installation, browser automation, or production deployment.
