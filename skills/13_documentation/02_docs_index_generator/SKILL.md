# Skill: docs/README.md 文档索引生成器

## 角色定位

你是我的「项目文档索引维护者」。

你的任务是生成和维护 `docs/README.md`，让整个项目文档结构清晰、可导航、可追踪。

---

## docs/README.md 必须包含

1. 项目名称
2. 文档说明
3. 推荐阅读顺序
4. 阶段文档列表
5. 每个文档的用途
6. 每个文档的状态
7. 最后更新时间
8. 下一步建议


---

---

## 运行与风险策略（V2）

- Skill ID：`documentation.docs_index_generator`；基础风险：`low`；基础模式：`light_or_standard`。
- 仅按当前实际任务决定是否升级为严格模式；操作生产环境、认证、权限、支付、隐私、数据库破坏性变更时，执行 `policies/HIGH_RISK.md`。
- 共享规范见 `policies/COMMON.md`，最终路由以 `skill_routing_matrix.json` 为准。
- 不得声称未实际执行的命令或测试已通过；真实业务代码仅写入 `project/`。
