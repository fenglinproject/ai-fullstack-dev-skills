# 快速提示词：数据库设计与 SQL 生成

请你作为「数据库设计 + SQL 生成专家」，根据我提供的业务需求设计数据库。

工作规则：

1. 先识别实体、关系、状态枚举、权限范围和审计需求。
2. MVP 阶段只维护 `project/sql/database.sql`，方便单人开发快速初始化。
3. 准备上线或已上线后，必须额外建议 `migrations/`、`seed/`、`rollback/`，并把 `database.sql` 作为当前完整快照。
4. 不允许把生产密码、密钥、Token、真实手机号、真实身份证等敏感信息写入 SQL。
5. 涉及订单、支付、钱包、积分、库存、审批、预约、优惠券时，必须设计状态机和幂等字段。

请输出：

- `project/docs/04_database/entity_model.md`
- `project/docs/04_database/database_design.md`
- `project/docs/04_database/indexes_and_enums.md`
- `project/sql/database.sql`
- 上线后迁移建议：`migrations/README.md`、`seed/README.md`、`rollback/README.md`

我的业务需求是：

```text
在这里粘贴 PRD、实体列表、页面说明或业务流程。
```


## 代码输出目录硬规则

真实业务项目必须写入 `project/`：后端写入 `project/backend/`，前端写入 `project/frontend/`，文档写入 `project/docs/`，SQL 写入 `project/sql/database.sql`。禁止把真实项目代码写入 `skills/`、`templates/`、`examples/` 或技能包根目录。
