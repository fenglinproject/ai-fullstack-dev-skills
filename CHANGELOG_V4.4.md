# V4.4 变更记录

## 目标

为可信的**已有本地 Git 仓库**提供只读接入和可靠性预检，而不是在缺少业务仓库授权的情况下自行连接账号、执行第三方代码或宣称已完成生产验证。

## 新增

- `tools/repo_readiness_v44.py`：本地 Git 仓库根目录和固定提交验证；静态技术栈信号；候选文件路径冲突和未完成变更审计；离线 CI JSON 与 HEAD 匹配校验；组合 `reviewable/needs_initialization/blocked` 预检状态。
- `tools/repo_trial_v44.py`：有界的重复只读采样，测量本地快照耗时、HEAD/状态一致性，并明确不是长期压力测试。
- `fullstack.py repo-readiness`、`repo-conflicts`、`repo-trial`：统一控制台入口及 CI 友好的退出码。
- `examples/v44-repo-demo/run_demo.py`：临时独立仓库、静态代码栈识别、离线 CI 结构和可靠性采样；测试执行需明确 `--execute-tests`，沿用可信 V4.3 的受控 Git 提交示例。
- `tests/test_v44.py`（27 项）：覆盖 Git 接入、CI 提交不匹配、失败状态、候选重叠、软链接、路径穿越、离线采样、CLI 退出码和信息最小化。
- GitHub Actions 中独立 V4.4 回归步骤。

## 兼容性

- 旧版 144 个 Skill、V3 审批/回退、V4.1 仪表盘和 V4.3 的 Git 审计均保留。
- `fullstack.py --version` 更新为 `4.4`，固定发布检查元数据版本更新。
- 本版不把 unsigned CI receipt 升级成可信 commit 证据；不修改原有验证与提交权限规则。

## 未实现

真实第三方仓库长期验证、CI 平台签名或认证 API、跨工作树原子锁、自动语义冲突合并、真实生产部署和全自动模型修复成功率验证。
