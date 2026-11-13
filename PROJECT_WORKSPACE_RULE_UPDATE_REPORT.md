# Project 工作区规则增强报告

## 本次目标

将真实业务项目代码与 Skills 工具包规则彻底分离：

- Skills 工具包：只放 Skill、模板、示例、路由和门禁。
- `project/`：只放真实业务项目代码、文档、SQL、测试和脚本。

## 新增目录

```text
project/
├── backend/
├── frontend/
├── docs/
├── sql/
├── tests/
├── scripts/
└── README.md
```

## 强制路径规则

| 类型 | 必须写入 |
|---|---|
| 后端代码 | `project/backend/` |
| 前端代码 | `project/frontend/` |
| 原生小程序 | `project/frontend/miniprogram/` |
| uni-app / H5 / Vue / React | `project/frontend/` |
| 业务文档 | `project/docs/` |
| 数据库 SQL | `project/sql/database.sql` |
| 测试 | `project/tests/` 或 `project/docs/07_testing/` |

## 禁止事项

- 禁止在技能包根目录直接创建 `backend/` 或 `frontend/`。
- 禁止把真实业务代码写入 `skills/05_backend/` 或 `skills/06_frontend/`。
- 禁止把真实业务代码写入 `templates/` 或 `examples/`。
- 禁止用业务项目 README 覆盖 Skills 工具包 README。

## 已更新的关键文件

- `00_MASTER_PROMPT.md`
- `START_HERE.md`
- `README.md`
- `SKILL_ROUTING_MATRIX.md`
- `skill_routing_matrix.json`
- `skills_index.json`
- `CORE_SKILL_VIEW.md`
- `skills/03_architecture/02_repo_structure_standard/SKILL.md`
- `skills/05_backend/00_backend_project_init/SKILL.md`
- `skills/06_frontend/00_frontend_project_init/SKILL.md`
- `skills/06_frontend/01_frontend_project_scaffold/SKILL.md`
- `skills/06_frontend/02_miniprogram_config_generator/SKILL.md`
- `skills/14_project_startup_docs/00_project_startup_docs_generator/SKILL.md`
- `templates/project_structure_template.md`
- `templates/start_here_template.md`
- `templates/docs_structure_template.md`
- `templates/sql_file_template.sql`

## 使用方式

后续可以直接对 AI 说：

```text
按这个技能包创建项目，真实代码全部放到 project/，后端放 project/backend/，前端放 project/frontend/。
```
