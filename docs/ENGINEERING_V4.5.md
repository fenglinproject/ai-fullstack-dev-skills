# V4.5 GitHub CI observation, cross-worktree reservation, repository sampling

## Goals and scope

- Preserve all 144 skills and pre-existing CLI commands.
- Distinguish local unsigned CI receipts from authenticated **live GitHub API observations**.
- Coordinate a single advisory writer across linked Git worktrees without automatic stale-lock stealing.
- Compare bounded, read-only samples from multiple trusted local Git repositories.

## 1. Remote CI check-run observation

```bash
# First pin a real Git HEAD from your trusted local Git repo:
git -C /path/to/repo rev-parse HEAD

# No network request, inspect the proposed request first:
python fullstack.py remote-ci --project /path/to/repo \
  --expected-head <40-character-sha> --required-check unit

# Requires gh installed, already authenticated with permission to read check runs:
python fullstack.py remote-ci --project /path/to/repo \
  --expected-head <40-character-sha> --required-check unit --execute
```

Only explicit `github.com` origin URLs and a current matching local HEAD are allowed. The GitHub CLI runs a GET against the pinned commit's check-runs API. Every named check must occur **exactly once**, be completed, and have a passing conclusion; missing, duplicate, pending or failing checks fail closed. Responses exceeding the first 100 checks are rejected rather than silently treated as complete. No GitHub write occurs. A successful observation is **not a cryptographically signed CI attestation**; it does not prove the workflow was trustworthy, that branch protection is satisfied, or authorize Git merging or deployment. Remote GitHub access was not tested with a personal account in this release; the authenticated CLI response was mocked in tests.

## 2. Shared worktree writer reservation

```bash
python fullstack.py worktree-lock status --project /path/to/repo
python fullstack.py worktree-lock acquire --project /path/to/repo --approve
# Save release_token to a secure location, avoid logging it or committing it.
python fullstack.py worktree-lock release --project /path/to/repo --token <release_token>
```

The lock resides in the **Git common directory** and is shared by Git linked worktrees. Creation is atomic (`O_EXCL`, restrictive permissions), and only its token holder can release it. A stale or corrupt lock requires manual resolution; the tool will not steal it automatically. **Important:** this is advisory coordination for cooperating processes, not a mandatory file-system lock or comprehensive protection for `workflow.apply`, Git CLI, or third-party editors. Do not assume unrelated writers are blocked.

## 3. Comparison across local repositories

```bash
python fullstack.py repo-compare --project /path/to/repo1 \
  --project /path/to/repo2 --samples 5
```

Up to eight independent local repositories and 20 samples each. The command does not clone repositories, install dependencies, execute their code, or contact remote services. It returns per-repository status consistency, pinned HEAD observations, blocker counts and median snapshot latency. These short samples do not establish long-term uptime or production safety.

## 4. Tests and trust boundaries

```bash
python -m unittest tests.test_v44 tests.test_v45 -v
python tools/audit_catalog.py
python tools/benchmark_router.py
```

Default permissions remain unchanged: remote CI requires explicit `--execute`, and acquiring a writer reservation requires `--approve`. No auto-push, merge, production deployment or external-model request is introduced. Known gaps: authenticated GitHub checks cannot prove CI workflow integrity; worktree reservations are not yet mandatory for all write paths; real third-party GitHub account operations and multi-day production soaks remain unverified.
