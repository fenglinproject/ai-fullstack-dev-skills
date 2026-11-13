# CHANGELOG V4.7 — 发布验收与故障注入

基于 V4.6 正式包升级，保留原 144 个 Skill，原始 ZIP 未修改。

- 新增 `tools/release_matrix_v47.py`：4 个不可随意注入测试模块的固定 shard、独立解释器、逐模块超时、总执行预算、报告摘要、源码 SHA-256、非通过状态严格拦截。
- 统一 CLI 增加 `fullstack.py release-matrix`，默认只做计划；只有 `--execute` 才运行随包可信测试。
- 新增 `tools/fault_injection_v47.py`：临时 Git 仓库中的多进程写入锁竞争、子进程硬终止、自动释放以及不安全 symlink gate 检查。
- 新增 `tests/test_v47.py`，覆盖上述新功能、超时、权限边界和报告输出路径校验。
- GitHub Actions 采用拆分的 CI 并行矩阵，并配置 Linux、Windows、macOS 锁故障演练（仅为工作流定义；线上执行效果另行验证）。
- 更新 `tools/release_gate.py` 的报告版本；统一 CLI 版本升级为 4.7。
- 更新历史 V4.0 的报告目录断言：验证预览前后状态不变化，而不是假定工作区绝无先前报告目录。

安全边界：工具的 OS 锁仅约束参与式写入流程；测试执行不是沙箱，不会主动使用真实 GitHub 账号、运行远程模型或部署生产环境。
