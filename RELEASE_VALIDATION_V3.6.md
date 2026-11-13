# AI Fullstack Dev Skills V3.6 — 发布验证

## 范围

本次是在 V3.5 全量功能与全部 144 个专业 Skill 基础上新增 Python AST 语法定位、日志路径线索和历史失败辅助上下文排序，并增加四项目固定离线评测。未取消审批、测试授权、回退、Git 权限及外部模型传输限制。

## 实际执行结果

| 检查 | 结果 | 说明 |
| --- | --- | --- |
| `python tools/sync_catalog.py --check` | 通过 | 索引与技能目录一致 |
| `python tools/audit_catalog.py` | 通过 | 144 个 Skill、30 个主入口、无失效引用或审计告警 |
| `python -m compileall -q orchestrator tools tests benchmarks/projects` | 通过 | Python 源码可编译 |
| `python -m unittest discover -s tests -q` | **185/185 通过** | 包含原有 166 项及新增 19 项 |
| `python tools/benchmark_router.py` | **28/28 技能 + 28/28 模式匹配** | 原有路由回归 |
| `python tools/benchmark_v35.py --min-recall 0.8 --min-triage 0.8` | 通过 | 原有 10 检索 + 8 分类基准 |
| `python tools/benchmark_v36.py --min-holdout 0.75` | **14/14 符号用例 + 8/8 路径用例** | 固定可见样例，分组结果见 `benchmarks/v36_results.json` |
| `examples/runnable-todo` API 单元测试 | **11/11 通过** | 保留旧样例功能 |
| `benchmarks/projects/inventory-service` 单元测试 | **1/1 通过** | 本次新增的合成示例 |
| `benchmarks/projects/notes-workspace` 单元测试 | **1/1 通过** | 本次新增的合成示例 |
| `examples/loop-demo/run_offline_demo.py` | 通过 | 两轮修复、第二轮通过、人工回退至原文件 |
| `agent.py context --symbol-hints` | 通过 | 已指定源码白名单，不自动增加源文件 |

## 解读限制

- 14/14 和 8/8 是 **随包且可见的固定离线样例**，并不代表真实生产项目、第三方隐藏测试集、真实 LLM 修复率或完整 LSP 精度。部分用例与实现开发处于同一轮调试过程，不能作为严格独立的外部测评。
- AST 仅覆盖 Python 静态语法定位；其他语言仍使用 V3.5 词项检索及此前静态依赖图。
- 测试执行器不等于经安全认证的隔离沙箱。本轮没有调用真实外部模型、没有使用 Docker，也没有真实 GitHub PR 创建、推送或生产部署操作。
- 机器的运行环境和示例文件只验证了上面实际运行的功能，不能推出所有兼容技术栈都已验证。
