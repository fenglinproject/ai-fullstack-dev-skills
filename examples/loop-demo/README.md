# V3.2 two-round offline repair demo

From the extracted repository root, run:

```bash
python examples/loop-demo/run_offline_demo.py
```

The script copies the shipped, trusted `examples/workflow-demo` into a temporary
folder, initializes `.ai/`, generates an initial **deliberately failing** patch,
applies it with explicit approval, runs trusted `unittest` checks, generates a
second offline repair proposal using the failure evidence, approves that edit,
retests successfully, and restores both changes in reverse order.

No API key, network call, package install, Git commit or push is used.
**This is a demonstration script that explicitly approves and runs code in its
own temporary project; it is NOT an untrusted-code sandbox.** Use the interactive
`orchestrator/loop.py` commands on real projects instead of bypassing review.
