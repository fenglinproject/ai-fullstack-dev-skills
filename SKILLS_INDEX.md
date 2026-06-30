# Skills Index

## 00_core：总控

| Skill | 用途 |
|---|---|
| 单人全栈开发总控 | 自动判断阶段并选择对应 Skill |

## 01_requirements：需求阶段

用于项目想法分析、需求澄清、MVP 范围、PRD、需求评审、验收标准。

## 02_product_design：产品设计阶段

用于页面结构、用户流程、交互状态、空状态、加载状态、错误状态。

## 03_architecture：技术架构阶段

用于技术栈选择、系统架构、目录结构、环境规划。

## 04_database：数据库阶段

用于实体建模、数据库设计、索引枚举和单 SQL 生成。

数据库阶段必须生成：

```text
docs/04_database/database_design.md
sql/database.sql
```

| Skill | 路径 | 用途 |
|---|---|---|
| 单 SQL 生成器 | `skills/04_database/09_sql_generation/SKILL.md` | 生成单个 `sql/database.sql` |

## 05_backend：后端开发阶段

用于登录注册、权限、CRUD、文件上传、支付回调、缓存、限流、事务、幂等。

## 06_frontend：前端开发阶段

用于页面开发、组件拆分、表单校验、接口对接、状态管理和适配。

## 07_integration_debugging：联调与排错

用于接口联调、跨域、Token、数据不一致、Bug 定位和日志分析。

## 08_testing：测试阶段

用于功能测试、异常测试、边界测试、权限测试、接口测试、回归测试。

## 09_security：安全阶段

用于登录安全、Token、越权、SQL 注入、XSS、CSRF、防刷、文件上传、支付回调和部署安全。

## 10_deployment_ops：部署运维阶段

用于服务器、域名、SSL、Nginx、部署、备份、回滚、监控。

## 11_iteration：迭代阶段

用于用户反馈、Bug 优先级、新需求评估、版本规划和发版说明。

## 12_code_quality：代码质量

用于代码审查、重构建议、性能优化、可维护性检查。

## 13_documentation：docs 文档生成

用于强制 AI 在每个开发阶段生成 Markdown 文档，并统一放到 `docs/` 目录。

| Skill | 路径 | 用途 |
|---|---|---|
| docs 文档总控生成器 | `skills/13_documentation/00_docs_orchestrator/SKILL.md` | 判断阶段并生成对应 docs 文档 |
| 阶段文档生成器 | `skills/13_documentation/01_stage_doc_generator/SKILL.md` | 把阶段结果整理成 Markdown |
| docs/README.md 文档索引生成器 | `skills/13_documentation/02_docs_index_generator/SKILL.md` | 维护项目文档索引 |
| 文档质量检查门禁 | `skills/13_documentation/03_doc_review_gate/SKILL.md` | 检查文档是否能指导开发 |

## 14_project_startup_docs：具体业务项目启动文档

用于生成具体业务项目的启动文档，不是 Skills 工具包说明。

必须生成：

```text
START_HERE.md
README.md
.env.example
docs/00_getting_started/
```

| Skill | 路径 | 用途 |
|---|---|---|
| 具体业务项目启动文档生成器 | `skills/14_project_startup_docs/00_project_startup_docs_generator/SKILL.md` | 生成业务项目启动说明 |
| .env.example 生成器 | `skills/14_project_startup_docs/01_env_example_generator/SKILL.md` | 生成环境变量示例 |
| getting_started 文档生成器 | `skills/14_project_startup_docs/02_getting_started_docs_generator/SKILL.md` | 生成本地启动、数据库、前后端、部署、排错文档 |
