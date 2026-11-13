# project：真实业务项目工作区

这个目录用于放置 AI 生成的真实业务项目代码和运行文件。

Skills 工具包中的 `skills/`、`templates/`、`examples/` 只作为流程、规范、模板和示例来源，不应该写入真实业务代码。

推荐结构：

```text
project/
├── backend/       # 后端真实项目代码
├── frontend/      # 前端真实项目代码；小程序/uni-app/H5 也放这里
├── docs/          # 业务项目文档
├── sql/           # 数据库 SQL，例如 database.sql
├── tests/         # 测试代码或测试数据
├── scripts/       # 本项目脚本
├── .env.example   # 示例环境变量
├── README.md      # 业务项目说明
└── START_HERE.md  # 业务项目启动说明
```

硬规则：

- 后端代码只能生成到 `project/backend/`。
- 前端代码只能生成到 `project/frontend/`。
- 小程序原生代码默认生成到 `project/frontend/miniprogram/`。
- uni-app / H5 / Vue / React 代码默认生成到 `project/frontend/`。
- 业务项目文档生成到 `project/docs/`。
- 数据库 SQL 生成到 `project/sql/database.sql`。
- 不要把真实业务代码写入 `skills/`、`templates/`、`examples/` 或技能包根目录。
