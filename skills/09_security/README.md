# 09_security Skills

本目录包含以下细粒度 Skill：

- [项目全量安全检查](./00_full_security_audit/SKILL.md)：对认证、权限、注入、XSS、CSRF、防刷、文件、支付、部署做总审计
- [登录注册安全检查](./01_auth_security_check/SKILL.md)：检查密码、验证码、登录失败、短信轰炸、账号枚举、弱密码
- [Token 与会话安全](./02_token_session_security/SKILL.md)：检查 Token 过期、刷新、退出、存储、多端、泄露风险
- [权限与越权检查](./03_rbac_overpermission_check/SKILL.md)：检查横向越权、纵向越权、数据范围、后台接口访问
- [SQL 注入检查](./04_sql_injection_check/SKILL.md)：检查原生 SQL、搜索筛选排序、拼接条件、ORM 使用风险
- [XSS 与 CSRF 检查](./05_xss_csrf_check/SKILL.md)：检查富文本、v-html、dangerouslySetInnerHTML、Cookie 登录态、Origin 校验
- [防刷与幂等安全](./06_rate_limit_idempotency_check/SKILL.md)：检查登录、短信、下单、支付、退款、抽奖、上传等防刷和重复提交
- [文件上传安全检查](./07_upload_security_check/SKILL.md)：检查类型、大小、后缀、MIME、路径穿越、可执行目录、恶意文件
- [敏感数据安全检查](./08_sensitive_data_check/SKILL.md)：检查密码、Token、手机号、身份证、密钥、日志、接口返回、备份
- [支付与回调安全检查](./09_payment_security_check/SKILL.md)：检查金额篡改、回调验签、幂等、订单归属、退款、对账
- [后台管理安全检查](./10_admin_panel_security_check/SKILL.md)：检查后台登录、管理员分级、操作日志、高危操作二次确认、IP 白名单
- [部署与服务器安全检查](./11_deploy_server_security_check/SKILL.md)：检查 HTTPS、防火墙、端口、数据库/Redis 暴露、debug、Nginx 信息泄露
- [日志与错误安全检查](./12_log_error_security_check/SKILL.md)：检查错误返回、堆栈、服务器路径、SQL、敏感参数泄露
- [上线安全门禁](./13_security_acceptance_gate/SKILL.md)：上线前判断哪些安全问题必须修，哪些可监控后修