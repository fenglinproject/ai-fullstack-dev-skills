# V3.8 — Large-repository analysis and honest evaluation

- Added `tools/monorepo_workspace.py` for static npm/yarn/pnpm workspace discovery and constrained workspace package glob interpretation. No package scripts execute.
- Extended `tools/incremental_index.py` to resolve simple workspace package imports across TS/JS packages. Existing V3.7 caches remain readable; import edges are recalculated from current manifests on every build.
- Added `tools/incremental_graph.py` for opt-in dependency graph snapshots, SHA-256 changes, edge deltas, transitive dependents, and conservative warning flags.
- Added `tools/lsp_import.py` to safely ingest offline LSP-style exported symbol location metadata; it is not a full LSP client and does not launch a server.
- Added `tools/benchmark_v38.py` for generated disposable monorepo timing and paired outcomes aggregation supplied by users. No external model calls.
- Added regression/security tests for manifest changes, traversal/symlinks, review boundaries, LSP URI restrictions, missing dependencies, change impacts, and paired outcome validation.
- Original 144 Skill assets, code-edit approval, repair loop boundaries, test authorization, Git checks and rollback retained.

Limitations: static JS/TS workspace resolution is partial; dynamic imports, aliases, path plugins, and conditional exports can escape analysis. Candidate tests never replace complete CI. No real external model or unknown large repository tested in this release.
