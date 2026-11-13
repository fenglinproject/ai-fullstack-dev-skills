# 10_deployment_ops Skills

本目录包含以下细粒度 Skill：

- [服务器准备](./00_server_prepare/SKILL.md)：准备系统、运行环境、防火墙、目录、用户权限
- [环境变量配置](./01_env_variables_config/SKILL.md)：整理本地/测试/生产环境变量、密钥、配置隔离
- [域名 SSL Nginx](./02_nginx_ssl_domain/SKILL.md)：配置域名解析、HTTPS、反向代理、静态资源、上传限制
- [前端打包部署](./03_frontend_deploy/SKILL.md)：打包前端、配置环境、上传静态资源、缓存策略
- [后端打包部署](./04_backend_deploy/SKILL.md)：编译后端、配置进程守护、日志、端口、健康检查
- [Docker 部署](./05_docker_deploy/SKILL.md)：用 Docker/Docker Compose 部署前后端、数据库、Redis、Nginx
- [数据库初始化与备份](./06_database_init_backup/SKILL.md)：初始化库表、基础数据、定时备份、恢复验证
- [灰度上线](./07_gray_release/SKILL.md)：小流量上线、观察日志、验证核心流程后全量
- [回滚方案](./08_rollback_plan/SKILL.md)：准备代码、数据库、配置、静态资源回滚策略
- [生产监控](./09_production_monitoring/SKILL.md)：监控 CPU、内存、磁盘、接口错误、日志、业务指标
- [运维手册](./10_operation_runbook/SKILL.md)：沉淀部署、重启、备份、恢复、排错、账号权限手册