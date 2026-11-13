# AI Fullstack Dev Skills — V4.6

## 实现

- 新增 `orchestrator/write_guard_v46.py`：Git common-dir 的 OS 排他操作锁，支持 linked worktree 跨进程串行写入，检测人工预留令牌；非 Git 项目仍保持旧管理规则。
- 旧 V4.5 `worktree-lock acquire/release` 改为持有共同操作锁，减少人工预留与自动操作之间的交错。
- `workflow.apply`、`workflow.restore`、`workflow.verify`、`git_collab.branch`、`git_collab.commit` 接入写入锁；CLI 支持 `--worktree-token`。
- 新增 `orchestrator/recovery_v46.py`：`prepared` 部分源码写入的只读状态诊断与经审批哈希保护回退；`commit` 不确定状态的提交树验证及经审批补记。
- Git 提交操作在 staging 前留下 `commit_transaction` 提交意图；提交成功后记录 Git SHA 与交易状态。
- 增加 `fullstack.py recover {prepared,commit}`；仓库健康检查会提示未完成的 Git 提交事务。
- 新增 `tests/test_v46.py`，涵盖真实 linked worktree 进程互斥、预留令牌、崩溃模拟、Git HEAD/索引/证据验证、回退过程和 CLI 只读行为。
- 保留 144 个 Skill、30 个主入口和既有的本地看板、路由、代码审查与修复循环。

## 验证边界

- 操作锁只保护本工具包参与的入口，**不是所有进程都必须遵守的系统写锁**。
- 无自动重试/覆盖冲突，无远程 push、合并、部署，也无生产级可信 CI 证明。
- 历史单命令全量测试在之前版本有超时案例；V4.6 完整 354 项通过分组执行，独立 Smoke 4/4 通过。
