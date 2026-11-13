# API 文档

| 方法 | 路径 | 权限 | 请求 | 响应 | 错误码 |
|---|---|---|---|---|---|
| POST | /api/auth/login | 游客 | 手机号/密码 | token/user | AUTH_FAILED |
| GET | /api/items | 登录用户 | page/pageSize/filter | list/total | UNAUTHORIZED |
| POST | /api/items | 登录用户 | 表单数据 | item | VALIDATION_ERROR |
