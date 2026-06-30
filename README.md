# AI 单人全栈开发 Skills 超细分版

这是为「一个人开发全栈项目」准备的超细分 AI Skills 合集。

本版特点：

- 从原来的阶段级 Skill，升级为任务级 Skill。
- 共 127 个 Skill。
- 覆盖需求、PRD、原型、UI、架构、数据库、后端、前端、联调、测试、安全、部署、运维、迭代、代码质量。
- 每个 Skill 都包含：
  - 角色定位
  - 触发场景
  - 必要输入
  - 标准输出
  - 执行流程 SOP
  - 输出格式
  - 质量门禁
  - 可复制提示词
  - 单人开发特别要求

## 推荐使用方式

1. 先复制 `00_MASTER_PROMPT.md` 给 AI。
2. 再把 `project_context_template.md` 填好。
3. 根据当前任务，打开对应目录下的 `SKILL.md`。
4. 把 Skill 里的「可复制使用提示词」发给 AI。
5. 每个阶段结束后，用 `00_core/02_stage_gate_reviewer` 做阶段门禁评审。

## 目录结构

```text
AI单人全栈开发Skills超细分版/
├── 00_MASTER_PROMPT.md
├── README.md
├── skills_index.json
├── AI单人全栈开发Skills超细分版.md
├── templates/
└── skills/
    ├── 00_core/
    ├── 01_requirements/
    ├── 02_product_design/
    ├── 03_architecture/
    ├── 04_database/
    ├── 05_backend/
    ├── 06_frontend/
    ├── 07_integration_debugging/
    ├── 08_testing/
    ├── 09_security/
    ├── 10_deployment_ops/
    ├── 11_iteration/
    └── 12_code_quality/
```

## 最重要的使用原则

不要一上来就写代码。  
先用需求、页面、数据库、接口、权限、安全、测试这些 Skill 把项目拆清楚，再逐个模块开发。
