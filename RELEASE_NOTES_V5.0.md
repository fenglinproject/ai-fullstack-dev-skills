# AI Fullstack Dev Skills V5.0

## Highlights

V5.0 introduces an **opt-in, locally managed software release lifecycle** while retaining all 144 specialized development Skills and the approval-based engineering workflows from previous versions.

### Added

- Side-by-side release installation, preview and explicit approval before applying updates.
- Trusted external SHA-256 checking and optional public-key signature verification.
- Integrity-checked version activation, rollback and persistent project workspace.
- Bounded migration of prior local project files into the managed workspace.
- Reproducible packaging helpers, supply-chain metadata and updated onboarding documentation.

### Verification

- 431/431 Python unit/workflow tests passed **when run in separate groups** in a local Linux environment.
- 28/28 routing cases and 4/4 smoke checks passed locally.
- Local install / V4.9-to-V5.0 upgrade / rollback and workspace preservation were exercised.

### Known limitations

- GitHub Actions cross-platform results have **not** been authenticated as passing in the published V5.0 validation record.
- Live `npm ci` for the locked TypeScript 5.9.3 toolchain and formal publisher signatures have not been verified here.
- Test execution is not a security sandbox; AI model calls and file writes require user authorization.
- Lifecycle rollback switches toolkit code but does not undo external deployments or business database migrations.

See [CHANGELOG.md](CHANGELOG.md), [Quick Start](docs/QUICKSTART_CN.md), [Engineering Guide](docs/ENGINEERING_V5.0.md), and [Validation Record](RELEASE_VALIDATION_V5.0.md).
