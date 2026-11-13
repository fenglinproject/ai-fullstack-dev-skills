# V4.0 — 统一开发控制台与实际工程验收

- 新增 `fullstack.py` 和 `orchestrator/console.py`：doctor、route、project、index、select-tests、lsp、check、benchmark、verify 一体化入口。
- 新增 `tools/doctor.py`：只读环境自检，明确区分必须与可选依赖，不触发安装。
- 改进 `tools/lsp_client.py`：支持 C/C++ 受限候选文件；定义查询前发送标准 `didOpen`；本地真实 clangd 定位通过。仍需用户授权启动，非沙箱。
- 新增 `tools/release_gate.py`：固定 smoke/full 验收矩阵，默认仅计划，显式执行才运行。错误、跳过、超时与通过分别记录；不执行用户提供的任意命令。完整验证按历史模块分进程运行。
- 新增 `tests/test_v40.py`：统一 CLI、无授权拒绝、C/C++ 路径安全、真实 clangd（条件运行）、从初始化到测试报告再到任务完成的 E2E 回归。
- 添加 V4.0 工程指南、安全说明、操作入口和发布验证记录。
- 保留 144 个 Skill 和 V3.9 所有既有入口；没有新增自动 Git push、自动 merge、生产部署、无人工审批写入或新的外部模型调用。
