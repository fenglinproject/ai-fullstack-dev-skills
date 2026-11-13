# V4.5 release validation — local execution

## Confirmed passing

- `python -m unittest tests.test_v44 tests.test_v45 -q`: **36/36** (27 prior + 9 new).
- `python tools/benchmark_router.py`: **28/28** skill + mode cases.
- `python tools/audit_catalog.py`: passes, 144 skills, no issues.
- `(cd examples/runnable-todo && python -m unittest discover -s tests -q)`: **11/11**.
- `python fullstack.py verify --profile smoke --execute`: **4/4**.
- `python fullstack.py --version`: 4.5.
- Tests using real local Git repositories and linked worktrees exercise locking and read-only comparison.

## Mocked, unverified, and timed out

- GitHub CI check-run responses were **mocked**; no authenticated GitHub account was accessed, and no signed CI provenance is claimed.
- Broad all-history regression attempt exceeded execution time; **NOT certified as a full suite pass**. Earlier version tests remain in the package for users' local CI.
- No actual multi-day production repository soak test was performed.
- The shared Git common-directory lock is **advisory only** and not yet integrated as mandatory enforcement in every code-writing command.
- No external model, remote PR creation, deployment, Docker runtime or unknown project scripts executed in this release.
