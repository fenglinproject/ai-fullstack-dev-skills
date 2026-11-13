**V4.2 长期稳定性与样例验收：** [ENGINEERING_V4.2.md](ENGINEERING_V4.2.md) — 统计覆盖范围、临时压力测试、实际 Todo 测试证据闭环。

**V4.1 可视化控制台：** [ENGINEERING_V4.1.md](ENGINEERING_V4.1.md) — 本地只读仪表盘、安全与访问令牌、使用与自测。

# 项目文档中心

- 文档根目录：`docs/`
- 维护方式：由 AI 根据 Skills 工作流持续生成和更新
- 使用对象：具体业务项目

---

## 执行模式与文档强度

| 模式 | 何时使用 | 是否强制更新文档 |
|---|---|---|
| 轻量模式 | 快速答疑、局部判断、小修改 | 否，只给建议 |
| 标准模式 | 正常阶段推进 | 阶段结束时更新 |
| 严格模式 | 支付、权限、安全、上线、数据库变更、复杂 Bug | 必须更新并输出门禁结论 |

---

## 推荐阅读顺序

1. `00_getting_started/`：项目启动说明
2. `01_requirements/requirements_brief.md`：需求概要
3. `01_requirements/mvp_scope.md`：MVP 范围
4. `01_requirements/prd.md`：产品需求文档
5. `02_product_design/page_structure.md`：页面结构
6. `03_architecture/tech_architecture.md`：技术架构
7. `04_database/database_design.md`：数据库设计
8. `05_api/api_spec.md`：接口文档
9. `06_development/development_plan.md`：开发计划
10. `07_testing/test_cases.md`：测试用例
11. `08_security/security_audit.md`：安全检查
12. `09_deployment/deployment_guide.md`：部署指南
13. `10_iteration/iteration_plan.md`：版本迭代计划

---

## 使用规则

- 轻量模式不强制生成文档，避免小问题流程过重。
- 标准模式在阶段结束时生成或更新对应 Markdown 文档。
- 严格模式必须同步输出测试、风险、回滚和上线门禁。
- 每次数据库结构变化，都要同步更新 `project/docs/04_database/database_design.md` 和 `project/sql/database.sql`。
- 上线后数据库变更必须进入 `migrations/`，不能只覆盖历史 SQL。
