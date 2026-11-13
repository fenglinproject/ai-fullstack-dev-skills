# Start here — V5.0

1. **Explore:** `python fullstack.py --help` and `python fullstack.py doctor`.
2. **Review the installation trust model:** read `docs/ENGINEERING_V5.0.md`, especially `--expected-sha256` and optional signature handling.
3. **Preview before installation:** `python fullstack.py lifecycle plan --home <empty-home> --archive <zip> --expected-sha256 <trusted-digest>`.
4. **Install only after checking:** change `plan` to `install` and add `--approve`; upgrades similarly use `upgrade --approve`.
5. **Keep business projects in `<home>/workspace`**; changing the active release must not rewrite workspace files.
6. **Verify:** `python fullstack.py lifecycle status --home <home> --integrity`; `python <home>/launch.py --version`.
7. **Test only in a trusted environment:** `python fullstack.py release-matrix --shard all --execute`.

More: `README.md`, `SECURITY.md`, `CHANGELOG_V5.0.md`, `RELEASE_VALIDATION_V5.0.md`.
