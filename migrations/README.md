# migrations 目录说明

MVP 阶段可以只维护 `project/sql/database.sql`。

一旦项目进入“准备上线 / 已上线 / 多环境协作”阶段，数据库变更必须迁移化：

```text
migrations/
├── 001_init.sql
├── 002_add_xxx_table.sql
└── 003_alter_xxx_column.sql
```

规则：

- 每个 migration 只做一组相关变更。
- 文件名必须包含递增序号和简短说明。
- 变更前必须备份数据。
- 需要同步更新 `project/sql/database.sql` 作为当前完整快照。
- 破坏性变更必须准备 `rollback/` 脚本或人工回滚方案。
