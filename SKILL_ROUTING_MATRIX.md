# Skill 路由总览（V2，自动生成）

> 唯一机器可读路由源：`skill_routing_matrix.json`。本文件仅作人类阅读索引。

| ID | 阶段 | 名称 | 基础风险 | 模式 |
|---|---|---|---|---|
| `core.project_orchestrator` | core | 项目总控官 | low | light_or_standard |
| `core.project_context_collector` | core | 项目上下文收集 | low | light_or_standard |
| `core.stage_gate_reviewer` | core | 阶段门禁评审 | low | light_or_standard |
| `core.scope_controller` | core | MVP 范围控制 | low | light_or_standard |
| `core.change_request_manager` | core | 需求变更管控 | low | light_or_standard |
| `core.document_deliverable_manager` | core | 文档交付管理 | low | light_or_standard |
| `requirements.idea_to_requirements` | requirements | 想法转需求 | low | light_or_standard |
| `requirements.user_role_permission_analysis` | requirements | 用户角色与权限分析 | high | strict |
| `requirements.business_process_mapping` | requirements | 业务流程梳理 | low | light_or_standard |
| `requirements.mvp_scope_definition` | requirements | MVP 范围定义 | low | light_or_standard |
| `requirements.prd_generator` | requirements | PRD 生成 | low | light_or_standard |
| `requirements.page_function_spec` | requirements | 页面功能说明 | low | light_or_standard |
| `requirements.business_rule_spec` | requirements | 业务规则定义 | high | strict |
| `requirements.exception_scenario_mining` | requirements | 异常场景挖掘 | low | light_or_standard |
| `requirements.acceptance_criteria_builder` | requirements | 验收标准生成 | low | light_or_standard |
| `requirements.requirements_review` | requirements | 需求评审 | low | light_or_standard |
| `requirements.requirement_change_order` | requirements | 需求变更单 | low | light_or_standard |
| `product_design.information_architecture` | product_design | 信息架构设计 | low | light_or_standard |
| `product_design.user_flow_design` | product_design | 用户流程设计 | low | light_or_standard |
| `product_design.wireframe_spec` | product_design | 低保真原型说明 | low | light_or_standard |
| `product_design.interaction_state_spec` | product_design | 交互状态设计 | low | light_or_standard |
| `product_design.form_design_rules` | product_design | 表单设计规则 | low | light_or_standard |
| `product_design.list_filter_pagination_design` | product_design | 列表筛选分页设计 | low | light_or_standard |
| `product_design.ui_style_guide` | product_design | UI 风格规范 | low | light_or_standard |
| `product_design.component_inventory` | product_design | 组件清单 | low | light_or_standard |
| `product_design.microcopy_prompt_text` | product_design | 提示文案设计 | low | light_or_standard |
| `product_design.design_review` | product_design | 设计评审 | low | light_or_standard |
| `architecture.tech_stack_selection` | architecture | 技术栈选型 | medium | standard |
| `architecture.frontend_ui_library_selection` | architecture | 前端 UI 组件库选型 | medium | standard |
| `architecture.architecture_blueprint` | architecture | 整体架构方案 | medium | standard |
| `architecture.repo_structure_standard` | architecture | 项目目录结构规范 | medium | standard |
| `architecture.environment_strategy` | architecture | 环境规划 | medium | standard |
| `architecture.auth_architecture` | architecture | 认证架构 | high | strict |
| `architecture.permission_model` | architecture | 权限模型 | high | strict |
| `architecture.api_standard` | architecture | 接口规范 | medium | standard |
| `architecture.error_handling_standard` | architecture | 异常处理规范 | medium | standard |
| `architecture.logging_monitoring_plan` | architecture | 日志与监控方案 | medium | standard |
| `architecture.cache_strategy` | architecture | 缓存策略 | medium | standard |
| `architecture.third_party_service_plan` | architecture | 第三方服务方案 | medium | standard |
| `architecture.security_architecture` | architecture | 安全架构方案 | high | strict |
| `database.entity_modeling` | database | 业务实体建模 | medium | standard |
| `database.table_design` | database | 数据表设计 | medium | standard |
| `database.relationship_design` | database | 表关系设计 | medium | standard |
| `database.index_design` | database | 索引设计 | medium | standard |
| `database.status_enum_design` | database | 状态枚举设计 | medium | standard |
| `database.data_permission_scope` | database | 数据权限字段设计 | high | strict |
| `database.migration_seed_plan` | database | 迁移与初始化数据 | high | strict |
| `database.audit_log_table_design` | database | 审计日志表设计 | medium | standard |
| `database.backup_recovery_design` | database | 备份与恢复设计 | high | strict |
| `database.sql_generation` | database | 单 SQL 生成器 | medium | standard |
| `api.api_design_orchestrator` | api | 接口设计总控 | medium | standard |
| `api.openapi_spec_generator` | api | OpenAPI 规范生成 | medium | standard |
| `api.endpoint_contract_design` | api | 接口契约设计 | medium | standard |
| `api.api_mock_validation` | api | 接口 Mock 与校验 | medium | standard |
| `backend.backend_project_init` | backend | 后端项目初始化 | medium | standard |
| `backend.unified_response_exception` | backend | 统一返回体与异常处理 | medium | standard |
| `backend.auth_login_register` | backend | 登录注册模块 | high | strict |
| `backend.rbac_role_menu` | backend | RBAC 角色权限菜单 | high | strict |
| `backend.crud_module_generator` | backend | 业务 CRUD 模块 | medium | standard |
| `backend.complex_business_logic` | backend | 复杂业务逻辑 | medium | standard |
| `backend.order_payment_flow` | backend | 订单支付流程 | high | strict |
| `backend.file_upload_storage` | backend | 文件上传与存储 | high | strict |
| `backend.callback_webhook_handler` | backend | 回调与 Webhook 处理 | high | strict |
| `backend.scheduler_job` | backend | 定时任务 | medium | standard |
| `backend.redis_cache_rate_limit` | backend | Redis 缓存与限流 | medium | standard |
| `backend.transaction_idempotency` | backend | 事务与幂等 | high | strict |
| `backend.backend_self_test` | backend | 后端自测 | medium | standard |
| `frontend.frontend_project_init` | frontend | 前端项目初始化 | medium | standard |
| `frontend.frontend_project_scaffold` | frontend | 前端项目初始化文件生成器 | medium | standard |
| `frontend.miniprogram_config_generator` | frontend | 小程序配置文件生成器 | medium | standard |
| `frontend.route_guard_permission` | frontend | 路由守卫与权限控制 | high | strict |
| `frontend.state_management` | frontend | 状态管理 | medium | standard |
| `frontend.api_client_wrapper` | frontend | 接口请求封装 | medium | standard |
| `frontend.base_components` | frontend | 基础组件封装 | medium | standard |
| `frontend.static_page_build` | frontend | 静态页面搭建 | medium | standard |
| `frontend.form_validation_submit` | frontend | 表单校验与提交 | medium | standard |
| `frontend.list_search_pagination` | frontend | 列表搜索筛选分页 | medium | standard |
| `frontend.error_empty_loading_states` | frontend | 空/加载/错误状态处理 | medium | standard |
| `frontend.mobile_pc_adaptation` | frontend | 多端适配 | medium | standard |
| `frontend.frontend_self_test` | frontend | 前端自测 | medium | standard |
| `integration_debugging.api_integration_plan` | integration_debugging | 接口联调计划 | medium | standard |
| `integration_debugging.network_error_debug` | integration_debugging | 网络请求错误排查 | medium | standard |
| `integration_debugging.cors_auth_debug` | integration_debugging | 跨域与鉴权排查 | medium | standard |
| `integration_debugging.data_mismatch_debug` | integration_debugging | 数据不一致排查 | medium | standard |
| `integration_debugging.payment_callback_debug` | integration_debugging | 支付回调排查 | high | strict |
| `integration_debugging.full_process_runthrough` | integration_debugging | 完整业务流程跑通 | medium | standard |
| `integration_debugging.bug_root_cause_analysis` | integration_debugging | Bug 根因分析 | medium | standard |
| `integration_debugging.regression_after_fix` | integration_debugging | 修复后回归 | medium | standard |
| `integration_debugging.systematic_debugging` | integration_debugging | 系统性调试 | medium | standard |
| `testing.test_plan` | testing | 测试计划 | medium | standard |
| `testing.functional_test_cases` | testing | 功能测试用例 | medium | standard |
| `testing.boundary_exception_cases` | testing | 边界与异常用例 | medium | standard |
| `testing.permission_test_cases` | testing | 权限测试用例 | high | strict |
| `testing.api_test_cases` | testing | 接口测试用例 | medium | standard |
| `testing.compatibility_test_cases` | testing | 兼容性测试 | medium | standard |
| `testing.performance_test_plan` | testing | 性能测试计划 | medium | standard |
| `testing.bug_report_template` | testing | Bug 报告模板 | medium | standard |
| `testing.regression_test_suite` | testing | 回归测试套件 | medium | standard |
| `testing.release_acceptance_test` | testing | 上线验收测试 | high | strict |
| `testing.test_driven_development` | testing | 测试驱动开发（TDD） | medium | standard |
| `security.full_security_audit` | security | 项目全量安全检查 | high | strict |
| `security.auth_security_check` | security | 登录注册安全检查 | high | strict |
| `security.token_session_security` | security | Token 与会话安全 | high | strict |
| `security.rbac_overpermission_check` | security | 权限与越权检查 | high | strict |
| `security.sql_injection_check` | security | SQL 注入检查 | high | strict |
| `security.xss_csrf_check` | security | XSS 与 CSRF 检查 | high | strict |
| `security.rate_limit_idempotency_check` | security | 防刷与幂等安全 | high | strict |
| `security.upload_security_check` | security | 文件上传安全检查 | high | strict |
| `security.sensitive_data_check` | security | 敏感数据安全检查 | high | strict |
| `security.payment_security_check` | security | 支付与回调安全检查 | high | strict |
| `security.admin_panel_security_check` | security | 后台管理安全检查 | high | strict |
| `security.deploy_server_security_check` | security | 部署与服务器安全检查 | high | strict |
| `security.log_error_security_check` | security | 日志与错误安全检查 | high | strict |
| `security.security_acceptance_gate` | security | 上线安全门禁 | high | strict |
| `deployment_ops.server_prepare` | deployment_ops | 服务器准备 | high | strict |
| `deployment_ops.env_variables_config` | deployment_ops | 环境变量配置 | high | strict |
| `deployment_ops.nginx_ssl_domain` | deployment_ops | 域名 SSL Nginx | high | strict |
| `deployment_ops.frontend_deploy` | deployment_ops | 前端打包部署 | high | strict |
| `deployment_ops.backend_deploy` | deployment_ops | 后端打包部署 | high | strict |
| `deployment_ops.docker_deploy` | deployment_ops | Docker 部署 | high | strict |
| `deployment_ops.database_init_backup` | deployment_ops | 数据库初始化与备份 | high | strict |
| `deployment_ops.gray_release` | deployment_ops | 灰度上线 | high | strict |
| `deployment_ops.rollback_plan` | deployment_ops | 回滚方案 | high | strict |
| `deployment_ops.production_monitoring` | deployment_ops | 生产监控 | high | strict |
| `deployment_ops.operation_runbook` | deployment_ops | 运维手册 | high | strict |
| `iteration.feedback_triage` | iteration | 用户反馈归类 | medium | standard |
| `iteration.version_planning` | iteration | 版本规划 | medium | standard |
| `iteration.hotfix_workflow` | iteration | 线上紧急修复 | high | strict |
| `iteration.backlog_grooming` | iteration | 需求池维护 | medium | standard |
| `iteration.release_notes` | iteration | 版本发布说明 | medium | standard |
| `iteration.handover_docs` | iteration | 交付文档沉淀 | medium | standard |
| `code_quality.code_review` | code_quality | 代码审查 | medium | standard |
| `code_quality.refactoring_plan` | code_quality | 重构计划 | medium | standard |
| `code_quality.git_branch_commit` | code_quality | Git 分支提交规范 | medium | standard |
| `code_quality.dependency_upgrade` | code_quality | 依赖升级检查 | high | strict |
| `code_quality.performance_optimization` | code_quality | 性能优化 | medium | standard |
| `code_quality.observability_logs` | code_quality | 可观测性与日志规范 | medium | standard |
| `documentation.docs_orchestrator` | documentation | docs 文档总控生成器 | low | light_or_standard |
| `documentation.stage_doc_generator` | documentation | 阶段文档生成器 | low | light_or_standard |
| `documentation.docs_index_generator` | documentation | docs/README.md 文档索引生成器 | low | light_or_standard |
| `documentation.doc_review_gate` | documentation | 文档质量检查门禁 | low | light_or_standard |
| `project_startup_docs.project_startup_docs_generator` | project_startup_docs | 具体业务项目启动文档生成器 | low | light_or_standard |
| `project_startup_docs.env_example_generator` | project_startup_docs | .env.example 生成器 | low | light_or_standard |
| `project_startup_docs.getting_started_docs_generator` | project_startup_docs | docs/00_getting_started 文档生成器 | low | light_or_standard |
