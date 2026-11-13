# 真实业务项目目录结构模板

默认所有业务代码和业务文档都放到 `project/`。

```text
project/
├── backend/
│   ├── package.json
│   ├── src/
│   ├── tests/
│   └── .env.example
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── src/
│   └── tests/
├── docs/
│   ├── 00_getting_started/
│   ├── 01_requirements/
│   ├── 02_product_design/
│   ├── 03_architecture/
│   ├── 04_database/
│   ├── 05_api/
│   ├── 06_development/
│   ├── 07_testing/
│   ├── 08_security/
│   ├── 09_deployment/
│   └── 10_iteration/
├── sql/
│   └── database.sql
├── tests/
├── scripts/
├── .env.example
├── README.md
└── START_HERE.md
```

禁止事项：

- 禁止在技能包根目录直接创建 `backend/` 或 `frontend/`。
- 禁止把业务代码写入 `skills/05_backend/` 或 `skills/06_frontend/`。
- 禁止把业务项目 README 覆盖 Skills 工具包 README。
