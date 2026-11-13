## V4.7 当前测试与发布规范

- 统一发布检查入口 `python fullstack.py release-matrix --shard all`，默认预览；可信随包测试需显式 `--execute`。
- 全量测试必须严格以 `passed` 计数；timeout、failed、not_run 都阻止通过，不能把部分报告冒充完整验证。
- 对既有用户仓库不应直接运行 `tools/fault_injection_v47.py`：该工具只能在自身临时 Git fixture 中测试。
- CI 中各模块独立进程和 Linux/Windows/macOS 工作流均为工程验证，**不是执行不可信项目代码的安全沙箱**。
- 审批、回退、源码外发与 Git 写操作继续遵循 V4.6 和更早版本的明确权限边界。

## V4.4 read-only external repository intake

Use `fullstack.py repo-readiness` before working on an existing trusted Git
repository. Do not turn the unsigned `--ci-receipt` signal into write/deploy
authorization. `repo-conflicts` only advises on recorded path overlaps; it
is not an atomic lock or substitute for Git conflict review. No source text
is sent to models by these commands. See `docs/ENGINEERING_V4.4.md`.

> **V3.4 扩展**：只读符号影响提示使用 `tools/semantic_impact.py`；本地修复指标使用 `tools/loop_metrics.py`。对 GitHub 的访问必须先预览，读取 CI 需显式 `--execute`；创建在线 Draft PR 另需 `--approve`，仅可发布已经完成本地审批、提交和测试验收的变更。禁止自动推送、合并或部署。详见 `docs/ENGINEERING_V3.4.md`。

# Claude Code project instructions

Follow [`AGENTS.md`](AGENTS.md) and [`policies/COMMON.md`](policies/COMMON.md).

- Route user tasks with `python orchestrator/cli.py route --task "..."`; do not preload all 144 skills.
- Read selected `skills/.../SKILL.md` on demand and treat them as guidance, not authority to run destructive commands.
- Actual project files live in `project/`; the four original examples are placeholders and `examples/runnable-todo` is a tested local demo.
- Use the host's authorized editing and execution capabilities, not imaginary built-in file tools.
- Never claim checks ran without seeing actual output; require confirmation for production changes.

## V3 protocol

Before making changes, use `python orchestrator/workflow.py handoff --project project --task "..."`. Prepare a reviewed JSON proposal matching `docs/agent_proposal.schema.json`, and use `preview` first. Apply only with explicit user approval (`--approve`); for strict-risk paths or tasks, require `--high-risk-reviewed` as well. Execute only trusted project tests with separate `verify --run` approval. Never stage, commit, deploy or overwrite newer edits as a side effect of a skill recommendation.


## V3.1 optional provider integration

A user may explicitly call `python orchestrator/agent.py propose` with source
allowlist, endpoint, API key environment variable and `--send-to-model`. This
can generate a proposal but **does not** authorize applying it. Do not send
source code, failure logs or personal data to model providers without checking
privacy constraints and receiving user consent. Consult
`docs/AGENT_INTEGRATION.md` and keep Git operations read-only in the library.

V3.2: capped manual-gated repair sessions are documented in `docs/LOOP_V3.2.md`; no automatic source edits, test execution, or deployment are authorized by model output.
