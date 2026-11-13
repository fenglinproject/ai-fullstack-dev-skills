# V4.5 change log

- Added `tools/remote_ci_v45.py`: explicitly authorized, pinned-commit GitHub check-run observations; fail closed for duplicate, missing, incomplete or failed checks.
- Added `tools/worktree_lock_v45.py`: Git common-directory advisory writer lock, requiring explicit acquisition approval and release token.
- Added `tools/repo_comparison_v45.py`: bounded read-only multi-repository reliability sampling.
- Exposed `remote-ci`, `worktree-lock`, and `repo-compare` via `fullstack.py`.
- Added nine V4.5 regression tests, preserved prior 144 skills.
- No automatic remote writes, source changes, merge or deployment.
