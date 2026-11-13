# 核心 Skill 视图：主 Skill + 子清单

本文件不删除原有 144 个 Skill，而是给 AI 和用户提供 20～30 个主视角，降低选择成本。

使用方法：先选主视角，再从子清单选择具体 Skill；高风险条目自动进入严格模式。

## 00. 项目总控与阶段门禁

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `core.project_orchestrator` / 项目总控官 | high | strict | 帮我做项目总控官、启动项目总控官 Skill |
| `core.project_context_collector` / 项目上下文收集 | high | strict | 帮我做项目上下文收集、启动项目上下文收集 Skill |
| `core.stage_gate_reviewer` / 阶段门禁评审 | high | strict | 帮我做阶段门禁评审、启动阶段门禁评审 Skill |
| `core.scope_controller` / MVP 范围控制 | high | strict | 帮我做MVP 范围控制、启动MVP 范围控制 Skill |
| `core.change_request_manager` / 需求变更管控 | high | strict | 帮我做需求变更管控、启动需求变更管控 Skill |
| `core.document_deliverable_manager` / 文档交付管理 | high | strict | 帮我做文档交付管理、启动文档交付管理 Skill |

## 01. 需求与 MVP

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `requirements.idea_to_requirements` / 想法转需求 | high | strict | 帮我做想法转需求、启动想法转需求 Skill |
| `requirements.user_role_permission_analysis` / 用户角色与权限分析 | high | strict | 帮我做用户角色与权限分析、启动用户角色与权限分析 Skill |
| `requirements.business_process_mapping` / 业务流程梳理 | high | strict | 帮我做业务流程梳理、启动业务流程梳理 Skill |
| `requirements.mvp_scope_definition` / MVP 范围定义 | high | strict | 帮我做MVP 范围定义、启动MVP 范围定义 Skill |
| `requirements.prd_generator` / PRD 生成 | high | strict | 帮我做PRD 生成、启动PRD 生成 Skill |
| `requirements.page_function_spec` / 页面功能说明 | high | strict | 帮我做页面功能说明、启动页面功能说明 Skill |
| `requirements.business_rule_spec` / 业务规则定义 | high | strict | 帮我做业务规则定义、启动业务规则定义 Skill |
| `requirements.exception_scenario_mining` / 异常场景挖掘 | high | strict | 帮我做异常场景挖掘、启动异常场景挖掘 Skill |
| `requirements.acceptance_criteria_builder` / 验收标准生成 | high | strict | 帮我做验收标准生成、启动验收标准生成 Skill |
| `requirements.requirements_review` / 需求评审 | high | strict | 帮我做需求评审、启动需求评审 Skill |
| `requirements.requirement_change_order` / 需求变更单 | high | strict | 帮我做需求变更单、启动需求变更单 Skill |

## 02. 产品设计与页面流程

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `product_design.information_architecture` / 信息架构设计 | high | strict | 帮我做信息架构设计、启动信息架构设计 Skill |
| `product_design.user_flow_design` / 用户流程设计 | high | strict | 帮我做用户流程设计、启动用户流程设计 Skill |
| `product_design.wireframe_spec` / 低保真原型说明 | high | strict | 帮我做低保真原型说明、启动低保真原型说明 Skill |
| `product_design.interaction_state_spec` / 交互状态设计 | high | strict | 帮我做交互状态设计、启动交互状态设计 Skill |
| `product_design.form_design_rules` / 表单设计规则 | high | strict | 帮我做表单设计规则、启动表单设计规则 Skill |
| `product_design.list_filter_pagination_design` / 列表筛选分页设计 | high | strict | 帮我做列表筛选分页设计、启动列表筛选分页设计 Skill |
| `product_design.ui_style_guide` / UI 风格规范 | high | strict | 帮我做UI 风格规范、启动UI 风格规范 Skill |
| `product_design.component_inventory` / 组件清单 | high | strict | 帮我做组件清单、启动组件清单 Skill |
| `product_design.microcopy_prompt_text` / 提示文案设计 | high | strict | 帮我做提示文案设计、启动提示文案设计 Skill |
| `product_design.design_review` / 设计评审 | high | strict | 帮我做设计评审、启动设计评审 Skill |

## 03. 架构与技术选型

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `architecture.tech_stack_selection` / 技术栈选型 | high | strict | 帮我做技术栈选型、启动技术栈选型 Skill |
| `architecture.frontend_ui_library_selection` / 前端 UI 组件库选型 | high | strict | 推荐前端组件库、前端组件库怎么选、管理后台用什么组件库 |
| `architecture.architecture_blueprint` / 整体架构方案 | high | strict | 帮我做整体架构方案、启动整体架构方案 Skill |
| `architecture.repo_structure_standard` / 项目目录结构规范 | high | strict | 帮我做项目目录结构规范、启动项目目录结构规范 Skill |
| `architecture.environment_strategy` / 环境规划 | high | strict | 帮我做环境规划、启动环境规划 Skill |
| `architecture.auth_architecture` / 认证架构 | high | strict | 帮我做认证架构、启动认证架构 Skill |
| `architecture.permission_model` / 权限模型 | high | strict | 帮我做权限模型、启动权限模型 Skill |
| `architecture.api_standard` / 接口规范 | high | strict | 帮我做接口规范、启动接口规范 Skill |
| `architecture.error_handling_standard` / 异常处理规范 | high | strict | 帮我做异常处理规范、启动异常处理规范 Skill |
| `architecture.logging_monitoring_plan` / 日志与监控方案 | high | strict | 帮我做日志与监控方案、启动日志与监控方案 Skill |
| `architecture.cache_strategy` / 缓存策略 | high | strict | 帮我做缓存策略、启动缓存策略 Skill |
| `architecture.third_party_service_plan` / 第三方服务方案 | high | strict | 帮我做第三方服务方案、启动第三方服务方案 Skill |
| `architecture.security_architecture` / 安全架构方案 | high | strict | 帮我做安全架构方案、启动安全架构方案 Skill |

## 04. 数据库与迁移

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `database.entity_modeling` / 业务实体建模 | high | strict | 帮我做业务实体建模、启动业务实体建模 Skill |
| `database.table_design` / 数据表设计 | high | strict | 帮我做数据表设计、启动数据表设计 Skill |
| `database.relationship_design` / 表关系设计 | high | strict | 帮我做表关系设计、启动表关系设计 Skill |
| `database.index_design` / 索引设计 | high | strict | 帮我做索引设计、启动索引设计 Skill |
| `database.status_enum_design` / 状态枚举设计 | high | strict | 帮我做状态枚举设计、启动状态枚举设计 Skill |
| `database.data_permission_scope` / 数据权限字段设计 | high | strict | 帮我做数据权限字段设计、启动数据权限字段设计 Skill |
| `database.migration_seed_plan` / 迁移与初始化数据 | high | strict | 帮我做迁移与初始化数据、启动迁移与初始化数据 Skill |
| `database.audit_log_table_design` / 审计日志表设计 | high | strict | 帮我做审计日志表设计、启动审计日志表设计 Skill |
| `database.backup_recovery_design` / 备份与恢复设计 | high | strict | 帮我做备份与恢复设计、启动备份与恢复设计 Skill |
| `database.sql_generation` / 单 SQL 生成器 | high | strict | 生成 SQL、生成建表语句 |

## 05. API 契约与 Mock

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `api.api_design_orchestrator` / 接口设计总控 | high | strict | 生成接口文档、设计 API |
| `api.openapi_spec_generator` / OpenAPI 规范生成 | high | strict | 生成接口文档、设计 API |
| `api.endpoint_contract_design` / 接口契约设计 | high | strict | 生成接口文档、设计 API |
| `api.api_mock_validation` / 接口 Mock 与校验 | high | strict | 生成接口文档、设计 API |

## 06. 认证与权限

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `requirements.user_role_permission_analysis` / 用户角色与权限分析 | high | strict | 帮我做用户角色与权限分析、启动用户角色与权限分析 Skill |
| `architecture.auth_architecture` / 认证架构 | high | strict | 帮我做认证架构、启动认证架构 Skill |
| `architecture.permission_model` / 权限模型 | high | strict | 帮我做权限模型、启动权限模型 Skill |
| `database.data_permission_scope` / 数据权限字段设计 | high | strict | 帮我做数据权限字段设计、启动数据权限字段设计 Skill |
| `backend.auth_login_register` / 登录注册模块 | high | strict | 帮我做登录注册模块、启动登录注册模块 Skill |
| `backend.rbac_role_menu` / RBAC 角色权限菜单 | high | strict | 帮我做RBAC 角色权限菜单、启动RBAC 角色权限菜单 Skill |
| `frontend.route_guard_permission` / 路由守卫与权限控制 | high | strict | 帮我做路由守卫与权限控制、启动路由守卫与权限控制 Skill |
| `integration_debugging.cors_auth_debug` / 跨域与鉴权排查 | high | strict | 帮我做跨域与鉴权排查、启动跨域与鉴权排查 Skill |
| `testing.permission_test_cases` / 权限测试用例 | high | strict | 帮我做权限测试用例、启动权限测试用例 Skill |
| `security.auth_security_check` / 登录注册安全检查 | high | strict | 帮我做登录注册安全检查、启动登录注册安全检查 Skill |
| `security.token_session_security` / Token 与会话安全 | high | strict | 帮我做Token 与会话安全、启动Token 与会话安全 Skill |
| `security.rbac_overpermission_check` / 权限与越权检查 | high | strict | 帮我做权限与越权检查、启动权限与越权检查 Skill |

## 07. 订单支付与高风险交易

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `backend.order_payment_flow` / 订单支付流程 | high | strict | 帮我做订单支付流程、启动订单支付流程 Skill |
| `backend.callback_webhook_handler` / 回调与 Webhook 处理 | high | strict | 帮我做回调与 Webhook 处理、启动回调与 Webhook 处理 Skill |
| `backend.transaction_idempotency` / 事务与幂等 | high | strict | 帮我做事务与幂等、启动事务与幂等 Skill |
| `integration_debugging.payment_callback_debug` / 支付回调排查 | high | strict | 帮我做支付回调排查、启动支付回调排查 Skill |
| `security.rate_limit_idempotency_check` / 防刷与幂等安全 | high | strict | 帮我做防刷与幂等安全、启动防刷与幂等安全 Skill |
| `security.payment_security_check` / 支付与回调安全检查 | high | strict | 帮我做支付与回调安全检查、启动支付与回调安全检查 Skill |

## 08. 后端业务实现

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `backend.backend_project_init` / 后端项目初始化 | high | strict | 帮我做后端项目初始化、启动后端项目初始化 Skill |
| `backend.unified_response_exception` / 统一返回体与异常处理 | high | strict | 帮我做统一返回体与异常处理、启动统一返回体与异常处理 Skill |
| `backend.auth_login_register` / 登录注册模块 | high | strict | 帮我做登录注册模块、启动登录注册模块 Skill |
| `backend.rbac_role_menu` / RBAC 角色权限菜单 | high | strict | 帮我做RBAC 角色权限菜单、启动RBAC 角色权限菜单 Skill |
| `backend.crud_module_generator` / 业务 CRUD 模块 | high | strict | 帮我做业务 CRUD 模块、启动业务 CRUD 模块 Skill |
| `backend.complex_business_logic` / 复杂业务逻辑 | high | strict | 帮我做复杂业务逻辑、启动复杂业务逻辑 Skill |
| `backend.order_payment_flow` / 订单支付流程 | high | strict | 帮我做订单支付流程、启动订单支付流程 Skill |
| `backend.file_upload_storage` / 文件上传与存储 | high | strict | 帮我做文件上传与存储、启动文件上传与存储 Skill |
| `backend.callback_webhook_handler` / 回调与 Webhook 处理 | high | strict | 帮我做回调与 Webhook 处理、启动回调与 Webhook 处理 Skill |
| `backend.scheduler_job` / 定时任务 | high | strict | 帮我做定时任务、启动定时任务 Skill |
| `backend.redis_cache_rate_limit` / Redis 缓存与限流 | high | strict | 帮我做Redis 缓存与限流、启动Redis 缓存与限流 Skill |
| `backend.transaction_idempotency` / 事务与幂等 | high | strict | 帮我做事务与幂等、启动事务与幂等 Skill |
| `backend.backend_self_test` / 后端自测 | high | strict | 帮我做后端自测、启动后端自测 Skill |

## 09. 前端实现与自测

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `frontend.frontend_project_init` / 前端项目初始化 | high | strict | 帮我做前端项目初始化、启动前端项目初始化 Skill |
| `frontend.frontend_project_scaffold` / 前端项目初始化文件生成器 | low | light_or_standard | 初始化前端项目、生成小程序前端 |
| `frontend.miniprogram_config_generator` / 小程序配置文件生成器 | high | strict | 小程序配置文件生成器 |
| `frontend.route_guard_permission` / 路由守卫与权限控制 | high | strict | 帮我做路由守卫与权限控制、启动路由守卫与权限控制 Skill |
| `frontend.state_management` / 状态管理 | high | strict | 帮我做状态管理、启动状态管理 Skill |
| `frontend.api_client_wrapper` / 接口请求封装 | high | strict | 帮我做接口请求封装、启动接口请求封装 Skill |
| `frontend.base_components` / 基础组件封装 | high | strict | 帮我做基础组件封装、启动基础组件封装 Skill |
| `frontend.static_page_build` / 静态页面搭建 | high | strict | 帮我做静态页面搭建、启动静态页面搭建 Skill |
| `frontend.form_validation_submit` / 表单校验与提交 | high | strict | 帮我做表单校验与提交、启动表单校验与提交 Skill |
| `frontend.list_search_pagination` / 列表搜索筛选分页 | high | strict | 帮我做列表搜索筛选分页、启动列表搜索筛选分页 Skill |
| `frontend.error_empty_loading_states` / 空/加载/错误状态处理 | high | strict | 帮我做空/加载/错误状态处理、启动空/加载/错误状态处理 Skill |
| `frontend.mobile_pc_adaptation` / 多端适配 | high | strict | 帮我做多端适配、启动多端适配 Skill |
| `frontend.frontend_self_test` / 前端自测 | high | strict | 帮我做前端自测、启动前端自测 Skill |

## 10. 联调与系统性调试

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `integration_debugging.api_integration_plan` / 接口联调计划 | high | strict | 帮我做接口联调计划、启动接口联调计划 Skill |
| `integration_debugging.network_error_debug` / 网络请求错误排查 | high | strict | 帮我做网络请求错误排查、启动网络请求错误排查 Skill |
| `integration_debugging.cors_auth_debug` / 跨域与鉴权排查 | high | strict | 帮我做跨域与鉴权排查、启动跨域与鉴权排查 Skill |
| `integration_debugging.data_mismatch_debug` / 数据不一致排查 | high | strict | 帮我做数据不一致排查、启动数据不一致排查 Skill |
| `integration_debugging.payment_callback_debug` / 支付回调排查 | high | strict | 帮我做支付回调排查、启动支付回调排查 Skill |
| `integration_debugging.full_process_runthrough` / 完整业务流程跑通 | high | strict | 帮我做完整业务流程跑通、启动完整业务流程跑通 Skill |
| `integration_debugging.bug_root_cause_analysis` / Bug 根因分析 | high | strict | 帮我做Bug 根因分析、启动Bug 根因分析 Skill |
| `integration_debugging.regression_after_fix` / 修复后回归 | high | strict | 帮我做修复后回归、启动修复后回归 Skill |
| `integration_debugging.systematic_debugging` / 系统性调试 | high | strict | 帮我系统性调试、不要乱改，按步骤排查 |

## 11. 测试与 TDD

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `testing.test_plan` / 测试计划 | high | strict | 帮我做测试计划、启动测试计划 Skill |
| `testing.functional_test_cases` / 功能测试用例 | high | strict | 帮我做功能测试用例、启动功能测试用例 Skill |
| `testing.boundary_exception_cases` / 边界与异常用例 | high | strict | 帮我做边界与异常用例、启动边界与异常用例 Skill |
| `testing.permission_test_cases` / 权限测试用例 | high | strict | 帮我做权限测试用例、启动权限测试用例 Skill |
| `testing.api_test_cases` / 接口测试用例 | high | strict | 帮我做接口测试用例、启动接口测试用例 Skill |
| `testing.compatibility_test_cases` / 兼容性测试 | high | strict | 帮我做兼容性测试、启动兼容性测试 Skill |
| `testing.performance_test_plan` / 性能测试计划 | high | strict | 帮我做性能测试计划、启动性能测试计划 Skill |
| `testing.bug_report_template` / Bug 报告模板 | high | strict | 帮我做Bug 报告模板、启动Bug 报告模板 Skill |
| `testing.regression_test_suite` / 回归测试套件 | high | strict | 帮我做回归测试套件、启动回归测试套件 Skill |
| `testing.release_acceptance_test` / 上线验收测试 | high | strict | 帮我做上线验收测试、启动上线验收测试 Skill |
| `testing.test_driven_development` / 测试驱动开发（TDD） | high | strict | 我要测试驱动开发、按 TDD 做这个功能 |

## 12. 安全审计

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `security.full_security_audit` / 项目全量安全检查 | high | strict | 帮我做项目全量安全检查、启动项目全量安全检查 Skill |
| `security.auth_security_check` / 登录注册安全检查 | high | strict | 帮我做登录注册安全检查、启动登录注册安全检查 Skill |
| `security.token_session_security` / Token 与会话安全 | high | strict | 帮我做Token 与会话安全、启动Token 与会话安全 Skill |
| `security.rbac_overpermission_check` / 权限与越权检查 | high | strict | 帮我做权限与越权检查、启动权限与越权检查 Skill |
| `security.sql_injection_check` / SQL 注入检查 | high | strict | 帮我做SQL 注入检查、启动SQL 注入检查 Skill |
| `security.xss_csrf_check` / XSS 与 CSRF 检查 | high | strict | 帮我做XSS 与 CSRF 检查、启动XSS 与 CSRF 检查 Skill |
| `security.rate_limit_idempotency_check` / 防刷与幂等安全 | high | strict | 帮我做防刷与幂等安全、启动防刷与幂等安全 Skill |
| `security.upload_security_check` / 文件上传安全检查 | high | strict | 帮我做文件上传安全检查、启动文件上传安全检查 Skill |
| `security.sensitive_data_check` / 敏感数据安全检查 | high | strict | 帮我做敏感数据安全检查、启动敏感数据安全检查 Skill |
| `security.payment_security_check` / 支付与回调安全检查 | high | strict | 帮我做支付与回调安全检查、启动支付与回调安全检查 Skill |
| `security.admin_panel_security_check` / 后台管理安全检查 | high | strict | 帮我做后台管理安全检查、启动后台管理安全检查 Skill |
| `security.deploy_server_security_check` / 部署与服务器安全检查 | high | strict | 帮我做部署与服务器安全检查、启动部署与服务器安全检查 Skill |
| `security.log_error_security_check` / 日志与错误安全检查 | high | strict | 帮我做日志与错误安全检查、启动日志与错误安全检查 Skill |
| `security.security_acceptance_gate` / 上线安全门禁 | high | strict | 帮我做上线安全门禁、启动上线安全门禁 Skill |

## 13. 部署运维与回滚

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `deployment_ops.server_prepare` / 服务器准备 | high | strict | 帮我做服务器准备、启动服务器准备 Skill |
| `deployment_ops.env_variables_config` / 环境变量配置 | high | strict | 帮我做环境变量配置、启动环境变量配置 Skill |
| `deployment_ops.nginx_ssl_domain` / 域名 SSL Nginx | high | strict | 帮我做域名 SSL Nginx、启动域名 SSL Nginx Skill |
| `deployment_ops.frontend_deploy` / 前端打包部署 | high | strict | 帮我做前端打包部署、启动前端打包部署 Skill |
| `deployment_ops.backend_deploy` / 后端打包部署 | high | strict | 帮我做后端打包部署、启动后端打包部署 Skill |
| `deployment_ops.docker_deploy` / Docker 部署 | high | strict | 帮我做Docker 部署、启动Docker 部署 Skill |
| `deployment_ops.database_init_backup` / 数据库初始化与备份 | high | strict | 帮我做数据库初始化与备份、启动数据库初始化与备份 Skill |
| `deployment_ops.gray_release` / 灰度上线 | high | strict | 帮我做灰度上线、启动灰度上线 Skill |
| `deployment_ops.rollback_plan` / 回滚方案 | high | strict | 帮我做回滚方案、启动回滚方案 Skill |
| `deployment_ops.production_monitoring` / 生产监控 | high | strict | 帮我做生产监控、启动生产监控 Skill |
| `deployment_ops.operation_runbook` / 运维手册 | high | strict | 帮我做运维手册、启动运维手册 Skill |

## 14. 迭代、代码质量与文档

| 子 Skill | 风险 | 模式 | 适用场景 |
|---|---|---|---|
| `iteration.feedback_triage` / 用户反馈归类 | high | strict | 帮我做用户反馈归类、启动用户反馈归类 Skill |
| `iteration.version_planning` / 版本规划 | high | strict | 帮我做版本规划、启动版本规划 Skill |
| `iteration.hotfix_workflow` / 线上紧急修复 | high | strict | 帮我做线上紧急修复、启动线上紧急修复 Skill |
| `iteration.backlog_grooming` / 需求池维护 | high | strict | 帮我做需求池维护、启动需求池维护 Skill |
| `iteration.release_notes` / 版本发布说明 | high | strict | 帮我做版本发布说明、启动版本发布说明 Skill |
| `iteration.handover_docs` / 交付文档沉淀 | high | strict | 帮我做交付文档沉淀、启动交付文档沉淀 Skill |
| `code_quality.code_review` / 代码审查 | high | strict | 帮我做代码审查、启动代码审查 Skill |
| `code_quality.refactoring_plan` / 重构计划 | high | strict | 帮我做重构计划、启动重构计划 Skill |
| `code_quality.git_branch_commit` / Git 分支提交规范 | high | strict | 帮我做Git 分支提交规范、启动Git 分支提交规范 Skill |
| `code_quality.dependency_upgrade` / 依赖升级检查 | high | strict | 帮我做依赖升级检查、启动依赖升级检查 Skill |
| `code_quality.performance_optimization` / 性能优化 | high | strict | 帮我做性能优化、启动性能优化 Skill |
| `code_quality.observability_logs` / 可观测性与日志规范 | high | strict | 帮我做可观测性与日志规范、启动可观测性与日志规范 Skill |
| `documentation.docs_orchestrator` / docs 文档总控生成器 | high | strict | 生成项目文档、文档放到 docs 里面 |
| `documentation.stage_doc_generator` / 阶段文档生成器 | high | strict | 阶段文档生成器 |
| `documentation.docs_index_generator` / docs/README.md 文档索引生成器 | low | light_or_standard | docs/README.md 文档索引生成器 |
| `documentation.doc_review_gate` / 文档质量检查门禁 | low | light_or_standard | 文档质量检查门禁 |
| `project_startup_docs.project_startup_docs_generator` / 具体业务项目启动文档生成器 | high | strict | 生成启动文档、项目怎么启动 |
| `project_startup_docs.env_example_generator` / .env.example 生成器 | high | strict | .env.example 生成器 |
| `project_startup_docs.getting_started_docs_generator` / docs/00_getting_started 文档生成器 | high | strict | docs/00_getting_started 文档生成器 |


## 全局真实项目目录规则

- Skills 包目录只保存流程、规范、模板和示例。
- 真实业务项目统一放入 `project/`。
- 后端真实代码：`project/backend/`。
- 前端真实代码：`project/frontend/`。
- 业务文档：`project/docs/`。
- 数据库 SQL：`project/sql/database.sql`。
