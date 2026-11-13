# AI Fullstack Dev Skills V5.0 — Product lifecycle / release management

## Scope and trust boundary

V5.0 adds a **local, side-by-side release manager**. It can inspect a release ZIP, install it into a managed home, upgrade by atomically switching the active release, restore a previous release, import a prior project workspace, and check installed-file hashes. Neither installation nor rollback runs project scripts, calls an AI model, accesses the network or uploads private files. The 144 specialized Skill files and all V4.9 editing/approval workflows remain available.

**Do not confuse integrity with provenance.** `--expected-sha256` must be independently obtained from a trusted source; hashing a file and then trusting that same unverified file proves only self-consistency. For greater assurance, supply a signature and a public key obtained and authenticated independently. Successful cryptographic verification proves possession of the corresponding private key, **not** ownership of a publisher identity. No publisher signature, verified GitHub runner, or platform attestation is bundled.

## Requirements

- Python 3.11 recommended, 3.10+ supported by project tooling. Core lifecycle uses only the standard library. No `pip install` is required.
- `Git`, `Node.js 22`, and locked `TypeScript 5.9.3` are needed only for relevant project tasks, not installing or rolling back a release.
- For optional RSA/ECDSA signature verification, install `openssl` and supply the operator-approved public key and `.sig` file.
- Managed install home must be an **empty directory** or a directory previously initialized by this tool. Never select the root of an existing project as the managed home.

## 1. Verify a release and install without overwriting old code

The following commands are executed from an unpacked **V5.0 source folder**. Use actual, absolute paths. The SHA displayed here is a placeholder; replace it with an independently verified 64-hex digest.

```bash
python fullstack.py lifecycle plan \
  --home /path/to/ai-fullstack-install \
  --archive /path/to/ai-fullstack-dev-skills-v5.0.zip \
  --expected-sha256 <64-lowercase-hex-digest>

# Only after reviewing the plan:
python fullstack.py lifecycle install \
  --home /path/to/ai-fullstack-install \
  --archive /path/to/ai-fullstack-dev-skills-v5.0.zip \
  --expected-sha256 <64-lowercase-hex-digest> --approve

python fullstack.py lifecycle status --home /path/to/ai-fullstack-install --integrity
python /path/to/ai-fullstack-install/launch.py --version
```

To install **V4.9 first and then upgrade to V5.0**, run the first install against the independently verified V4.9 ZIP. Then run:

```bash
python fullstack.py lifecycle upgrade \
  --home /path/to/ai-fullstack-install \
  --archive /path/to/ai-fullstack-dev-skills-v5.0.zip \
  --expected-sha256 <64-lowercase-hex-digest> --approve
```

For a signed release, add both `--public-key /trusted/path/release-public.pem` and `--signature /path/to/release.zip.sig`. The CLI refuses to infer publication trust from an unsigned JSON provenance document or locally self-computed hash.

## 2. Rollback without deleting the newer release

```bash
python fullstack.py lifecycle rollback --home /path/to/ai-fullstack-install
python fullstack.py lifecycle rollback --home /path/to/ai-fullstack-install --approve
```

The previous version directory remains installed. Rollback changes the managed active-version pointer, not source files, Git history or database schemas. It verifies old installed-file hashes before switching. A manually edited/compromised old release is not silently restored. To upgrade again after rollback, use the V5.0 source CLI (earlier installed versions may not support lifecycle commands).

## 3. Preserve user projects separately from software releases

Managed layout:

```text
ai-fullstack-install/
  launch.py                     # stable entry point (calls selected version)
  .release-manager/state.json   # active version and local history
  releases/v4.9-<digest16>/     # immutable distribution, never edit here
  releases/v5.0-<digest16>/     # new distribution
  workspace/                    # your persistent projects and private state
```

Never keep business data in a versioned `releases/` directory. V5.0 never deletes the `workspace/` tree during upgrade or rollback.

To copy a project from a prior extracted version (for example, its `project/` folder) without changing the source:

```bash
python fullstack.py lifecycle import-workspace \
  --home /path/to/ai-fullstack-install \
  --source /path/to/old-v49/project --name project-from-v49

# Confirm the file count, then explicitly approve:
python fullstack.py lifecycle import-workspace \
  --home /path/to/ai-fullstack-install \
  --source /path/to/old-v49/project --name project-from-v49 --approve
```

For imports, symbolic links and existing target names are rejected. Files are copied with bounded limits. **Review copied private files and keep them out of release ZIPs**. This is a file import, not automatic schema/data migration. Business database migration remains a separate, operator-controlled process.

## 4. Locked release operations and interruption recovery

The manager uses a per-installation exclusive `operation.lock`. Partial extraction is staged before the version directory becomes visible, and the active pointer is written through a temporary file followed by atomic replacement. If a process is killed during an operation, the previously active version remains active. An orphan staged directory or operation lock may remain.

**Do not delete `operation.lock` automatically.** First check that no installation/upgrade process is running and that the installation home is not used by another operator. Inspect incomplete `.staging-*` paths manually. The tool does not try to guess whether a concurrent process died or is still active.

The lifecycle manager does not prevent editing version directories outside its own commands. `lifecycle status --integrity` detects changed or missing expected release files, but is not a tamper-proof OS-level permission control. Multiple instances modifying the install home outside this CLI are unsupported.

## 5. Check, build and verify the V5.0 distribution

```bash
python fullstack.py supply-chain audit
python fullstack.py release-package-v50 --output /path/to/dist/ai-fullstack-dev-skills-v5.0.zip
python fullstack.py release-package-v50 --output /path/to/dist/ai-fullstack-dev-skills-v5.0.zip --execute
python fullstack.py release-package-v50 --verify /path/to/dist/ai-fullstack-dev-skills-v5.0.zip
python fullstack.py release-matrix --shard all --execute
```

The packager produces a deterministic ZIP and a SHA-256 sidecar. Its manifest checks every included source file. It refuses archive path traversal, symlinks, and suspected private keys. A sidecar is **not** a publisher signature. V5.0 continues to support the V4.9 legacy release tool for testing existing archives.

For signatures and CycloneDX SBOM use `python fullstack.py supply-chain --help`. The `provenance` output remains **unsigned self-reported metadata** unless an independently trusted process signs and attests it.

## 6. CI and operating system coverage

V5.0's existing GitHub Actions workflow now executes the install/upgrade/rollback tests on its Linux, Windows and macOS lock-test matrix, and adds the new test module to the Linux full regression. It uses the existing eight-evidence aggregation gate, so a failing lifecycle test prevents downstream evidence from being produced. The source code, workflow YAML, and local Python regression have been checked here; **no real GitHub-hosted Windows/macOS CI run or production signing identity has been validated in this session**.

## 7. Verification limitations

- The install manager validates a release archive; it does not execute, build or verify arbitrary user projects. Use trusted local/isolated runners for project testing.
- New features are local tooling, not an automatically registered operating-system-wide package, Windows MSI installer or macOS signed application.
- Rollback swaps active tool versions, not application databases or remote deployments.
- The manager's lock only governs participants using this manager; it cannot block an external editor, process or other user with filesystem access.
