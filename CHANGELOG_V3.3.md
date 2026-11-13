# V3.3 — 工程协作与隔离测试适配

1. 新增 `tools/isolated_checks.py`：有容量限制的源码快照、Docker 运行命令白名单、网络关闭、只读挂载、非 root、资源限制；需要明确 `--run` 和摘要固定镜像。无 Docker 时拒绝执行，不回退到主机运行。
2. 新增 `tools/dependency_graph.py`：Python 和 JS/TS 本地静态导入及反向影响路径，最多 6 层；不执行源码。
3. 新增 `orchestrator/code_review.py`：基于已批准变更记录的静态风险提示与依赖影响汇总，不做自动安全批准。
4. 新增 `orchestrator/git_collab.py`：本地特性分支、具备变更哈希与测试证据门槛的显式批准提交、离线 PR Markdown 草稿。无推送/线上 PR/自动合并。
5. 更新 `orchestrator/workflow.py` 和 `orchestrator/loop.py`：可通过 `--isolated-image` 选择 Docker 快照测试（未指定则保留可信本机测试）。
6. 新增 `tests/test_v33.py`，扩充 Git、静态分析、隔离命令结构和工作流报告兼容测试。
7. 更新 CI、启动指南、隐私安全说明和发布验证记录。

**说明**：在本次构建环境中不存在 Docker 可执行文件。容器的真实运行和逃逸防护并未验证，不能把模拟测试宣称为真实 Docker 测试。Git 的本地操作与工作流测试已在临时仓库执行。
