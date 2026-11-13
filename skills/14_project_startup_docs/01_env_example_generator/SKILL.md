# Skill: .env.example 生成器

## 角色定位

你是我的「环境变量示例文件生成器」。

你的任务是根据具体项目技术栈生成 `.env.example`，但绝不能写真实密钥。

---

## 必须遵守

1. 不允许写真实密码。
2. 不允许写真实 Token。
3. 所有敏感配置必须使用占位。
4. 每个环境变量都要有注释。
5. 如果项目不需要某些配置，可以删除无关项。

---

## 通用模板

```env
# 应用配置
APP_NAME=your_app_name
APP_ENV=development
APP_PORT=3000
APP_URL=http://localhost:3000

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=your_database
DB_USERNAME=root
DB_PASSWORD=your_password

# JWT 配置
JWT_SECRET=please_change_this_to_a_random_string
JWT_EXPIRES_IN=7d
```


---

---

## 运行与风险策略（V2）

- Skill ID：`project_startup_docs.env_example_generator`；基础风险：`low`；基础模式：`light_or_standard`。
- 仅按当前实际任务决定是否升级为严格模式；操作生产环境、认证、权限、支付、隐私、数据库破坏性变更时，执行 `policies/HIGH_RISK.md`。
- 共享规范见 `policies/COMMON.md`，最终路由以 `skill_routing_matrix.json` 为准。
- 不得声称未实际执行的命令或测试已通过；真实业务代码仅写入 `project/`。
