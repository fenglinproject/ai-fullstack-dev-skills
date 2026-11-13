# 技术栈适配目录

- `python-sqlite.json`: 实际有可运行示例并已执行 API 单元测试。
- `vue3-node-postgres.json`: Vue 3 + TypeScript + Node.js + PostgreSQL 设计配方，未安装或端到端验证。
- `react-node-postgres.json`: React + Node + PostgreSQL 配方，未验证。
- `python-fastapi-postgres.json`: FastAPI + PostgreSQL 配方，未验证。

适配规则：不同技术栈可选不同测试命令，不应在非 MySQL 项目上强制运行 MySQL；生产变更必须单独授权。
