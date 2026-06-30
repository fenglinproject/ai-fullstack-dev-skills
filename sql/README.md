# SQL 目录说明

本目录只保留一个 SQL 文件：

```text
sql/database.sql
```

`database.sql` 包含：

1. 数据库基础设置
2. 建表 SQL
3. 索引 SQL
4. 初始化数据
5. 后续迁移记录

默认执行方式：

```bash
mysql -u 用户名 -p 数据库名 < sql/database.sql
```

注意：

- 不要把生产环境真实密码、密钥、Token 写入 SQL。
- 默认管理员密码必须使用哈希或占位。
- 每次修改数据库结构，都要同步更新 `docs/04_database/database_design.md`。
