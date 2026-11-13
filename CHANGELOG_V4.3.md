# V4.3 — 独立 Git 仓库验证与可靠性

- 新增 `tools/repo_health_v43.py`：只读仓库审计、可选固定 Git HEAD/干净工作区要求、任务验收证据及报告 SHA-256 校验、变更记录检测和历史提交快照验证；明确有界扫描。
- `orchestrator/workflow.py` 在验证后保存 `last_verification`，包含最近的报告哈希、执行状态、修改文件哈希与验证时 HEAD。最近验证失败将阻断使用旧报告提交。
- `orchestrator/git_collab.py` 提交前校验关联报告完整性与源码哈希，确保验证时 HEAD 未被替换；受控提交后记录 `committed` 和对应 Git SHA。
- `orchestrator/github_ci.py` 支持新的已提交状态，同时维持本地记录/HEAD/工作区干净与明确线上发布审批的检查。
- 新增 `examples/v43-repo-demo`：一次性临时仓库内真实 Git 分支、3–5 轮代码修改、测试、验收、提交、本地 PR 草稿和只读快照；默认仅预览。
- 新增 `tests/test_v43.py`（18 项），覆盖报告篡改、重试失败、HEAD 变化、历史提交、路径/软链接安全、CLI 返回码及 3 轮真实本地 Git 流程。
- 统一 CLI 新增 `audit-repo`；更新 Smoke 版本标记及 GitHub Actions 独立集成测试步骤。
- 保留原 144 个 Skill。**不包含真实生产项目评测、自动 Git 推送/合并、未经授权代码执行或真实外部 AI 模型调用。**
