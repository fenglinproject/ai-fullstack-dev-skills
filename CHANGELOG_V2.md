# V2 变更日志和验证范围

## P0: 目录与路由
- 保留所有 144 个 `SKILL.md`；移除各文件末尾重复、无关的高风险验证模板，改为引用共享政策。
- 统一 `skill_routing_matrix.json` 的风险分级：low 32 / medium 67 / high 45；动态按任务提升严格程度。
- 将 41 处无效 `testing.integration_test` 引用指向已存在的 `testing.api_test_cases`；移除无意义自引用和普通任务的泛用安全/数据库后置项。
- 重新生成 `SKILL_ROUTING_MATRIX.md`；增加元数据校验和 30 个主技能入口。

## P1: 执行支持
- `orchestrator/cli.py`：静态技能匹配、任务风险、项目上下文初始化、任务状态存取。
- `project/.ai/`：上下文、决策、进度、已知问题、变更日志与检查命令模板。
- `tools/run_checks.py`：受限验证命令执行器，支持 dry-run、明确执行以及可选 JSON 记录。
- `AGENTS.md`、`CLAUDE.md`、Cursor project rule：指导具有代码权限的外部编程代理如何执行最小变更闭环。
- `tools/audit_catalog.py`、`tools/benchmark_router.py`：从关键词式评分改为结构审计与确定性回归任务。

## P2: 样例与生态
- 增加离线可运行的 SQLite + Python + Web Todo 示例；包含用户注册、登录与任务级服务端授权。
- 增加 Vue/Node/PostgreSQL、React/Node/PostgreSQL、FastAPI/PostgreSQL 的技术栈配方（未经部署验证）。
- 增加自动化测试及 GitHub Actions CI 配置（远端 CI 运行结果未验证）。

## 测试解释
- 静态审计检查完整性和引用，不测真实 AI 开发能力。
- 28 个路由样本是精心设计的正例，不是代表性真实世界分布。
- API 单元测试使用 Python 标准库和本地临时 SQLite，未开展压力、安全攻防或公网部署测试。
- 工具默认不能自主创建业务代码；须依赖具备授权文件系统和终端能力的编程代理。
