# rollback 目录说明

用于保存数据库和发布回滚脚本。

推荐规则：

- 每个高风险 migration 都要有对应 rollback 说明。
- 数据删除、字段删除、类型收窄等破坏性变更必须人工确认。
- 回滚脚本需要在测试环境演练。

示例：

```text
rollback/
├── 002_add_xxx_table_rollback.sql
└── 003_alter_xxx_column_rollback.md
```
