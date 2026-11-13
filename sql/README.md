# SQL 目录说明

## MVP 阶段

MVP / 原型阶段默认只保留一个 SQL 文件：

```text
sql/database.sql
```

`database.sql` 包含：

1. 数据库基础设置
2. 建表 SQL
3. 索引 SQL
4. 状态枚举注释
5. 初始化数据样例
6. 当前完整 schema 快照

默认执行方式：

```bash
mysql -u 用户名 -p 数据库名 < sql/database.sql
```

---

## 上线后阶段

一旦项目进入“准备上线 / 已上线 / 多环境协作”阶段，不再只依赖单 SQL 文件，必须增加：

```text
migrations/
seed/
rollback/
```

规则：

- `sql/database.sql`：保留为当前完整 schema 快照。
- `migrations/`：记录每次结构变更。
- `seed/`：保存开发、测试、演示初始化数据。
- `rollback/`：保存高风险变更的回滚脚本或回滚说明。

---

## 安全注意事项

- 不要把生产环境真实密码、密钥、Token 写入 SQL。
- 默认管理员密码必须使用哈希或占位。
- 不要写入真实用户隐私数据。
- 每次修改数据库结构，都要同步更新 `docs/04_database/database_design.md`。
