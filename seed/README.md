# seed 目录说明

用于保存开发、测试、演示环境的初始化数据。

禁止写入：

- 生产真实用户数据
- 真实手机号、身份证、地址
- 真实密钥、Token、密码明文

推荐结构：

```text
seed/
├── dev_seed.sql
├── test_seed.sql
└── demo_seed.sql
```
