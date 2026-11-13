# V5.0 — Product lifecycle and installation safety

- Added `tools/lifecycle_v50.py`: independently pinned archive verification, optional publisher-key signature validation, side-by-side installation, atomic active release switch, installed integrity status, reversible release selection and bounded private workspace import.
- Added CLI `fullstack.py lifecycle {status,plan,install,upgrade,rollback,import-workspace}`; mutating operations require `--approve`.
- Added `tools/package_release_v50.py` and `tools/supply_chain_v50.py` for deterministic V5.0 release archives, source dependency policy, unverified provenance record, SBOM and optional operator signing.
- Added `tests/test_v50.py` with attack-path and end-to-end lifecycle tests; included it in the isolated test matrix and the cross-platform GitHub workflow.
- Adjusted version metadata, V5.0 engineering documentation and onboarding.
- Preserved 144 existing specialized Skill files and previous releases' editing/approval functionality.

**Boundaries:** CI YAML is not actual GitHub run evidence; an unsigned hash/provenance file is not publisher authentication. Lifecycle rollback does not reverse user database migrations or external deployments. No automatic remote publishing or unattended installation is added.
