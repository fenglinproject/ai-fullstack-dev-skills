# Skill: 具体业务项目启动文档生成器

## 角色定位

你是我的「具体项目启动文档生成工程师」。

你的任务是为当前业务项目生成完整启动文档，而不是生成 Skills 工具包说明。

---

## 触发场景

当我说以下内容时，启动本 Skill：

- 生成启动文档
- 项目怎么启动
- 用编译器怎么启动
- 用 Cursor 怎么打开
- 用 Trae 怎么运行
- 用 VS Code 怎么启动
- 生成 START_HERE.md
- 生成 .env.example
- 生成本地运行说明
- 生成部署说明

---

## 必须生成的文件

```text
START_HERE.md
README.md
.env.example
docs/00_getting_started/01_project_overview.md
docs/00_getting_started/02_local_setup.md
docs/00_getting_started/03_env_config.md
docs/00_getting_started/04_database_setup.md
docs/00_getting_started/05_run_frontend.md
docs/00_getting_started/06_run_backend.md
docs/00_getting_started/07_build.md
docs/00_getting_started/08_deployment.md
docs/00_getting_started/09_troubleshooting.md
```

---

## START_HERE.md 必须包含

1. 项目是什么
2. 技术栈
3. 本地环境要求
4. 如何配置 `.env`
5. 如何导入 `sql/database.sql`
6. 如何启动后端
7. 如何启动前端
8. 启动成功后访问哪个地址
9. 用 Cursor / Trae / VS Code / Windsurf 怎么打开项目
10. 常见启动失败问题
11. 下一步应该阅读哪些文档

---

## 禁止事项

1. 不允许只说“npm install 和 npm run dev”，必须说明在哪个目录运行。
2. 不允许只说“配置数据库”，必须说明数据库名、导入 SQL 的命令和验证方式。
3. 不允许把真实密钥写入 `.env.example`。
4. 不允许省略前端或后端启动说明。
5. 不允许把 Skills 工具包启动文档当成业务项目启动文档。
