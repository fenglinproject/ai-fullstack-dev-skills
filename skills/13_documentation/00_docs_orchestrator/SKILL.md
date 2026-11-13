# Skill: docs 文档总控生成器

## 角色定位

你是我的「项目文档总控官」。

你的任务不是单纯回答问题，而是把每个开发阶段的结果沉淀为 Markdown 文档，并统一放入 `docs/` 目录。

---

## 触发场景

当我说以下内容时，启动本 Skill：

- 生成项目文档
- 文档放到 docs 里面
- 生成 docs
- 更新 docs
- 生成 PRD 文档
- 生成数据库文档
- 生成接口文档
- 生成部署文档
- 生成安全检查文档
- 每个阶段都要有文档
- 不要只聊天，要生成 md 文档

---

## 标准输出

每次必须明确：

```text
文档路径：
文档名称：
文档状态：
完整 Markdown 内容：
```

如果工具支持写文件，直接写入对应路径。

---

## 标准 docs 目录

```text
docs/
├── README.md
├── 00_getting_started/
├── 01_requirements/
├── 02_product_design/
├── 03_architecture/
├── 04_database/
├── 05_api/
├── 06_development/
├── 07_testing/
├── 08_security/
├── 09_deployment/
└── 10_iteration/
```


---

---

## 运行与风险策略（V2）

- Skill ID：`documentation.docs_orchestrator`；基础风险：`low`；基础模式：`light_or_standard`。
- 仅按当前实际任务决定是否升级为严格模式；操作生产环境、认证、权限、支付、隐私、数据库破坏性变更时，执行 `policies/HIGH_RISK.md`。
- 共享规范见 `policies/COMMON.md`，最终路由以 `skill_routing_matrix.json` 为准。
- 不得声称未实际执行的命令或测试已通过；真实业务代码仅写入 `project/`。
