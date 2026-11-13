# Skill 合并建议

当前包保留细分 Skill，便于精确调用；但长期维护建议把 139+ 个 Skill 收敛为 20～40 个高质量 Skill。

## 一、建议合并方向

| 目标高阶 Skill | 可合并的现有 Skill | 说明 |
|---|---|---|
| 项目总控与阶段门禁 | `00_core/*`、`13_documentation/*` | 总控、上下文、范围、变更、文档索引可统一管理 |
| 需求与 PRD | `01_requirements/*` | 需求澄清、MVP、PRD、验收标准合并为一个强 PRD Skill |
| 产品设计 | `02_product_design/*` | 页面、流程、表单、列表、状态、文案合并 |
| 架构与技术栈 | `03_architecture/*` | 技术栈、架构、目录、环境、缓存、日志、安全架构 |
| 认证与权限 | `03_architecture/04_auth_architecture`、`03_architecture/05_permission_model`、`05_backend/02_auth_login_register`、`05_backend/03_rbac_role_menu`、`06_frontend/03_route_guard_permission`、`09_security/01-03` | 登录、Token、Session、RBAC、路由守卫、越权检查统一 |
| 数据库设计 | `04_database/*` | 实体、表、关系、索引、枚举、迁移、审计、备份 |
| API 契约 | `05_api/*`、`03_architecture/06_api_standard`、`08_testing/04_api_test_cases` | OpenAPI、错误码、Mock、契约测试 |
| 后端模块开发 | `05_backend/*` | CRUD、业务逻辑、事务、幂等、缓存、任务 |
| 前端模块开发 | `06_frontend/*` | 脚手架、状态、API 封装、组件、表单、列表、适配 |
| 支付与资金安全 | `05_backend/06_order_payment_flow`、`09_security/09_payment_security_check`、`07_integration_debugging/04_payment_callback_debug` | 订单、支付、回调、退款、对账、补偿 |
| 系统性调试 | `07_integration_debugging/*` | 网络、跨域、Token、数据不一致、根因分析、回归 |
| TDD 与测试 | `08_testing/*` | 测试计划、用例、权限、接口、回归、发布验收 |
| 安全审计 | `09_security/*` | 上线前安全门禁 |
| 部署与运维 | `10_deployment_ops/*` | 服务器、Nginx、Docker、备份、灰度、回滚、监控 |
| 迭代与代码质量 | `11_iteration/*`、`12_code_quality/*` | 反馈、版本、Hotfix、Review、重构、性能、可观测性 |

## 二、推荐落地方式

第一阶段：保留现有细分 Skill，但重建完整索引和触发词。

第二阶段：新增 20～40 个高阶 Skill，每个高阶 Skill 内部引用现有细分 Skill。

第三阶段：逐步废弃重复 Skill，只保留高质量入口。
