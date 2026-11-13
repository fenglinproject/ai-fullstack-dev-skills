# V3.3 Release Validation

**日期**：2026-11-06（本地构建环境）

## 已真实运行的验证

| 检查 | 结果 | 备注 |
|---|---|---|
| `python -m unittest discover -s tests -q` | **121/121 通过** | 旧版测试 + 新增工程协作测试 |
| `python tools/benchmark_router.py` | **28/28 技能命中，28/28 风险模式命中** | 预设基准 |
| `python tools/sync_catalog.py --check` | **通过** | 索引一致 |
| `python tools/audit_catalog.py` | **通过** | Skill 目录与引用 |
| `examples/runnable-todo` API unittest | **11/11 通过** | 本地 API 单元测试 |
| Python `compileall` | **通过** | orchestrator、tools、tests 和示例脚本 |
| 真实本地临时 Git 仓库集成测试 | **通过** | 分支创建、申请审批、Git commit、跳过 hooks、生成离线 PR 草稿、拒绝未审核修改 |
| Docker 快照命令构造和模拟运行 | **通过** | 验证资源限制、只读挂载、无网络、镜像摘要与无 Docker 时关闭执行 |

## 未验证的能力

- **当前环境没有 Docker CLI**：不声称已经在真实容器中执行测试或验证隔离强度；依赖可信宿主守护程序和可信镜像。
- **没有访问 GitHub/GitLab API**：只生成本地 PR 草稿，不创建线上 PR、不推送、不合并。
- **没有外部大模型 API 密钥**：此次没有验证第三方模型真实调用，原有离线测试仍然通过。
- **没有生产部署测试**：本版本不负责生产环境操作。
- **静态依赖扫描和风险检查只是启发式**：无法代替语义语言服务、专业静态检查或安全审计。

## 稳定性与兼容性

- 原有 **144 个 Skill** 保留。
- 原有 `run_checks.py` 可信本机测试仍可用；仅明确传入 `--isolated-image` 才使用新的可选 Docker 模式。
- V3.2 的逐轮人工审批、证据报告和安全回退保留。
- Git commit 必须另行显式批准，并且必须有与 `change_id` 关联的实际已执行且全通过的测试报告。
