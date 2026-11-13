## V4.6 cooperative writer lock and crash recovery

- The shared Git common-dir OS lock protects ONLY participating toolkit entrypoints. Uncooperative editors, bare Git, custom scripts and malicious code can ignore it. Do not treat it as a sandbox or as proof of cross-machine coordination.
- A V4.5 human reservation is enforced by those entrypoints; keep the 64-character token private. The OS operation lock is auto-released after a process exits, but a human reservation needs explicit release.
- `recover` defaults to **read-only** and requires approval to change state. Prepared file recovery never overwrites edits whose hashes differ from both recorded before and after states; ambiguous Git commit recoveries require manual resolution.
- The local `.ai/` journal and SHA-256 checks are not tamper-proof, cryptographically signed evidence. A local adversary with file-system access can alter both record and source.
- Explicit test execution runs trusted project code and may invoke arbitrary processes through dependencies, import hooks or build tools. Isolation requires an independently configured container/VM.

---

## V4.5 security boundaries

- `remote-ci` requests are **live authenticated GitHub API observations**, not signed provenance. Requires explicit `--execute`; no network calls otherwise.
- `worktree-lock` is advisory; it does not stop uncooperative writers or guarantee process identity. Never publish release tokens.
- `repo-compare` only reads metadata; bounded sampling is not a production load test.
- No remote merge, push, deploy, or automatic model invocation is permitted by these features.

# V4.2 本地看板的长期运行安全边界

任务总数按完整任务状态文件统计；超过展示上限的记录不向浏览器返回，证据与报告质量指标只覆盖展示样本并明确标注。新增压力测试默认只写系统临时目录；使用 `--project` 只读既有项目，不会执行项目代码。只有随包 Todo 演示显式带 `--execute-tests` 时才会运行可信 Python 单元测试（它不是安全沙箱）。仍禁止未经授权的源码修改、Git 远程操作和模型外发。

---

# V4.1 控制台安全说明

`fullstack.py dashboard` 仅在 127.0.0.1 提供本地只读网页，使用随机访问令牌与 HttpOnly/SameSite=Strict Cookie，默认阻止远程访问、HTML 脚本注入及网页写请求。它不是安全沙箱；同一台机器上的恶意进程或有权限的浏览器插件仍可能读取元数据。项目路径、任务名称及 Git 文件名会展示给本机浏览器，但不返回源码、补丁、凭据、模型输入、测试输出或备份。请勿共享令牌、代理端口到公网或在不可信环境运行 Git/LSP/测试命令。完整细节见 [V4.1 工程指南](docs/ENGINEERING_V4.1.md)。

---

## V3.5 本地检索与失败诊断安全补充

- 默认不联网。检索结果只产生候选上下文，可能包含未被正则识别的私人数据；外传前必须人工查看明确选择的文件。`--auto-context --send-to-model` 组合被拒绝。
- 忽略链接文件、常见凭据文件、`.ai` 私有记录及依赖/构建缓存。源码和错误日志均视为不可信数据，不能成为执行系统命令的依据。
- 对本地扫描设置文件总数、字节、单文件和结果数量限制，超限报错。安全规则属于基于约定的防护，不是恶意项目代码执行沙箱。
- 修复分类和基准评测不会实际执行命令。固定样例结果不构成安全审计或生产可用性证明。

# Security and Execution Boundary

This repository provides *instructions, routing metadata and development helpers*.
It does **not** provide a secure operating-system sandbox or production-grade
autonomous agent. Never run tests from an untrusted repository: Python unittest
modules can execute arbitrary code even when their invocation matches the allowlist.

- `tools/run_checks.py` is preview-only by default. `--run` is an explicit opt-in.
- Supported built-in checks are `python -m unittest discover` and `node --check FILE`.
  Arbitrary npm scripts, unknown Python modules, shell commands, deployments, and
  package installation are outside this runner's scope.
- Before executing, inspect the project's source, third-party packages, test
  fixtures, and `.ai/checks.json`. To test untrusted code use a separately
  provisioned locked-down container or VM without host secrets or network.
- Verification reports are local records, not tamper-proof attestations. A
  successful test in one revision does not certify later changes.
- `--manual-reason` is explicitly **human attestation**, not an automated test.
- Do not store secrets in examples, checks, or task records. Run real production
  actions only through reviewed project-specific deployment processes.
- For vulnerability reports, avoid opening an issue with live credentials;
  contact the maintainer via an appropriate private channel.

## V3 proposal workflow

- JSON proposals from an AI model or any third party are **untrusted input**. Preview
  and inspect every diff before `apply --approve`.
- `apply` and `restore` only modify reviewed UTF-8 text with explicit approval;
  neither gives production authorization. Protected paths and symlinks are refused.
- `.ai/changes/` stores local **unencrypted snapshots** for rollback. Restrict access
  to local users and avoid modifying secrets via this workflow.
- Hash-pinned source checks reject stale proposals; after an applied change is edited
  again, `restore` refuses to overwrite that work. This is not a filesystem sandbox,
  and it does not prevent external concurrent processes from modifying files.
- A passed test covers its specific code and environment. Tests themselves can
  execute arbitrary code and must never be run against untrusted projects on a host
  with secrets or elevated privileges.

- Strict-risk task summaries or sensitive code paths require **both** `--approve`
  and `--high-risk-reviewed` before local edits. This is a human attestation,
  not an independent security review or permission to deploy.

## V3.1 remote-model integration and diagnostics

- `orchestrator/agent.py` sends selected **source text** and project/task context
  to a configured provider **only** with `--send-to-model`. Inspect all selected
  files and the task description yourself. Never send proprietary source to an
  unapproved third-party endpoint. Remote model providers may log data under
  their own retention and privacy policies.
- Secrets are blocked by a **best-effort** scanner, not comprehensive DLP. A
  source file with an unfamiliar credential format, user data, or embedded
  prompts can still be sent. Never rely on this heuristic as authorization.
- API keys are read from an environment variable and not saved in output,
  manifests or proposals. Endpoints must use HTTPS unless an explicit loopback
  HTTP override is supplied. Redirects are rejected.
- AI-generated proposals must match the V3 schema, update only explicitly
  included source files, and use pinned current hashes. New-file paths require
  approved directory prefixes. Further explicit human approval is required
  before any source write.
- Failed test outputs can include private information. Diagnostics are bounded,
  but review test reports before using `--report` with a remote model.
- `orchestrator/git_review.py` is read-only and does not authorize commits or
  pull requests. Tests still execute trusted project code and are NOT sandboxed.

- Project initialization creates `.ai/.gitignore` to prevent accidental staging
  of local proposals, source backups and test logs. Existing Git indexes or
  explicit force-add commands are not undone: check `git status` yourself.

## V3.2 bounded repair sessions

- `orchestrator/loop.py` persists `.ai/loops/` session metadata and does not
  save API keys. Journals, proposals, model outputs, code backups and logs
  are local private data; protect all `.ai/` contents from untrusted users.
- Every iteration requires explicit `approve --approve` to write source and
  `test --trust-project-code` to execute trusted repository tests. External
  model calls require opt-in *each round*. Even allowlisted Python tests can
  run arbitrary code; use a real sandbox/VM for untrusted code.
- Loops cap rounds at 1–5, refuse modified proposals and stale source, and
  refuse to overwrite newer edits during reverse rollback. Failed test evidence
  is SHA-256-checked before requesting a repair; hashes do not prevent a local
  attacker who can edit both evidence and session state.
- A process crash while applying changes is reconciled against a recorded
  operation ID. Ambiguous or incomplete manifests halt in `recovery_needed`
  rather than executing an automatic unsafe recovery. Tests interrupted during
  execution may have side effects: `resume` does not silently rerun them.
- `--approve` records an operator attestation, not proof of independent human
  review. A malicious or untrusted wrapper can pass approval flags; protect
  access to the CLI and project directory.

## V3.3 Git, static review and Docker snapshot execution

- Docker tests are **opt-in**, require a trusted digest-pinned image and correctly secured daemon. The snapshot strips known sensitive names; it is NOT comprehensive secret detection. Other source files can contain secrets. The container uses disabled network, readonly root/source, no added caps and resource limits; this cannot guarantee containment.
- Never expose the Docker socket to the container. Do not run untrusted images, or use this tool on hosts with a Docker daemon accessible by untrusted users. No automatic fallback to host execution exists if Docker is unavailable.
- Local Git branch and commit tools require explicit approval and a trusted repository. Hooks are disabled for the commit, but Git config/filters can still invoke programs during indexing. Only reviewed files are staged. Never assume any remote PR, push, merge or production action occurred.
- Test reports and source backups are user-modifiable local files, not cryptographically trusted attestations. Code-review findings and import analysis are incomplete heuristics.

## V3.8 local repository analyzers
- Monorepo workspace discovery reads only bounded local JSON and a restricted static pnpm YAML section. No npm/yarn/pnpm installation or lifecycle scripts are executed.
- Dependency graph snapshots are opt-in metadata under `.ai/cache`, protected against symlink cache paths and written by atomic replacement. Their contents are untrusted for security-critical decisions.
- The optional LSP importer consumes offline JSON exports only. It does not launch LSP servers; file URIs must point to indexed, allowed project source paths and cannot grant model-sharing permission.
- Generated monorepo benchmarks contain no real user or model outcome data. Candidate test selection does not authorize skipping CI or security testing.

## V3.9 LSP 与外部仓库

- 不会自动寻找/启动第三方语言服务器；启动需指定绝对路径及 `--allow-start`。语言服务器本身可能执行代码或访问网络，**不是沙箱**。仅对可信程序和可信项目使用。
- LSP 输出为不可信元数据，只返回索引内源文件定位；不授予任何文件修改审批。
- 只读 Git 仓库评测禁止自动克隆/执行脚本，要求提交 SHA 和干净工作区；评测输出须位于被测仓库外。
- 静态项目配置解析可能遗漏条件导出/动态依赖；发布前仍需完整测试。

## V4.0 统一控制台安全边界

- `fullstack.py` 默认只读，`project init`/状态变更、`index --save-cache`、`check --execute`、`verify --execute` 和 `lsp --allow-start` 各自有显式权限边界。
- 真实 clangd 验证只表明已连接一个可信的本地语言服务器；启动 LSP 可执行第三方代码，绝非容器或安全隔离。`didOpen` 会将指定源码内容提供给该本地进程，**不会自动向外部大模型发送**。
- `verify` 是固定随包测试矩阵。标记为 passed 的步骤表示在该环境和该版本实际运行成功；超时和 skipped 不得计为通过。
- 非沙箱测试不应执行恶意仓库代码。固定标签的 Git 基准不执行仓库脚本，也不代表真实 AI 修复成功率。


## V4.3 新增本地证据检查边界

受控 Git 提交需要最近一份实际测试通过的报告、该报告的 SHA-256、对应代码内容哈希，以及一致的 Git 基线；历史 `committed` 变更按提交快照审核。**同一文件系统上的 SHA-256 记录只能发现部分篡改，不能防止有权限者同时修改报告和清单**。如需可信审计应结合外部 CI 签名和独立托管日志。`audit-repo` 只读但会调用 Git；仅用于可信仓库。随包 demo 在临时副本执行 Python 测试，不是容器安全沙箱，也不代表未知大型仓库验证。


## V4.4 existing repository intake

- Read-only Git commands and metadata scans are intended for **trusted local repositories**. Repository Git config and attribute/filter behavior may still be unsafe when handling malicious repositories; do not treat this as a sandbox.
- `repo-conflicts` is advisory and does not reserve a path or prevent a race. Review candidate paths again before modifying files and use separate branches and human authorization.
- JSON CI receipts are explicitly **unsigned and unauthenticated** even when their SHA-256 is printed and the commit matches. Never use them as approval for a write, deployment, or Git commit; verify status on the original trusted provider separately.
- All new tools refuse symlinked CI files, excessive reports, malformed manifests and unsafe candidate paths; read-only Git status output is bounded.
- `repo-trial` runs no test commands. Its performance samples are local, short and not long-running production evidence.


## V4.7 发布验收与故障注入安全边界

- `release-matrix` 默认预览，`--execute` 仅运行本工具包中固定列举的测试模块；每个模块使用隔离**进程**，而不是安全沙箱或受限容器。对不可信的附带代码，仍有运行风险。
- 模块启动前严格核对测试清单；超时、失败或未执行都不能作为通过证据。输出报告的本地 SHA-256 并非独立签名。
- 测试日志截断只是降低输出量，不能保证消除日志里的凭证，请保护 CI 工件权限。
- 故障注入只创建临时 Git fixture，且必须显式授权；不杀死或修改已有业务项目进程。
- Windows/macOS 兼容性的 CI 配置不等于已经完成对应操作系统的实际运行验证。

## V4.9 软件供应链边界

V4.9 使用固定 SHA 的 Action 引用与含 SRI 的 npm lockfile，防止不可审计的自动依赖漂移，但不构成第三方依赖的全面漏洞审计。`provenance.json` 为 unsigned、自声明的本地元数据。请勿将测试时生成的临时 OpenSSL 私钥用于正式发布；实际签名应由正式发布方掌握并保护私钥。验证时必须先通过可信渠道获得公钥。生产发布前应在 GitHub Actions 真正执行 Linux/Windows/macOS 验收，并根据需要接入 GitHub Artifact Attestations / Sigstore 的平台签名流程。

## V5.0 managed installation and updates

V5.0's release manager rejects path traversal, Windows-reserved names, case-colliding ZIP entries, symbolic links, mismatched per-file hashes, oversized archives and unmanaged non-empty install homes. It requires an expected SHA-256 digest on every install/upgrade and an explicit `--approve` for writes. A signature is optional and trusted **only when the operator authenticated the supplied public key separately**.

Installed release copies are versioned and never overwritten. Workspaces reside outside the releases tree. Rollback changes the active release pointer; it does not roll back project database contents or remote state. If an update is interrupted, inspect any residual `operation.lock` and `.staging-*` directories before manual cleanup, and do not force-remove a lock used by another process.
