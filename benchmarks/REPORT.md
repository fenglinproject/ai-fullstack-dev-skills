# 路由器基准测试

样本：28；Top-1 命中：28/28；模式命中：28/28。

该结果只代表设计的基准样例，不代表真实复杂项目中的 AI 成功率。

| 任务 | 预期 | 实际 | 模式 | 结果 |
|---|---|---|---|---|
| 修改按钮颜色 | `frontend.static_page_build` | `frontend.static_page_build` | light | PASS |
| 写一份PRD | `requirements.prd_generator` | `requirements.prd_generator` | standard | PASS |
| 生成一份MVP范围定义 | `requirements.mvp_scope_definition` | `requirements.mvp_scope_definition` | standard | PASS |
| 我要选技术栈 | `architecture.tech_stack_selection` | `architecture.tech_stack_selection` | standard | PASS |
| 设计数据库表结构 | `database.table_design` | `database.table_design` | standard | PASS |
| 数据库索引设计 | `database.index_design` | `database.index_design` | standard | PASS |
| 数据库迁移 | `database.migration_seed_plan` | `database.migration_seed_plan` | strict | PASS |
| 写一份OpenAPI接口文档 | `api.openapi_spec_generator` | `api.openapi_spec_generator` | standard | PASS |
| 新增文件上传接口 | `backend.file_upload_storage` | `backend.file_upload_storage` | strict | PASS |
| 实现用户注册登录 | `backend.auth_login_register` | `backend.auth_login_register` | strict | PASS |
| 实现用户权限管理 | `backend.rbac_role_menu` | `backend.rbac_role_menu` | strict | PASS |
| 实现支付退款接口 | `backend.order_payment_flow` | `backend.order_payment_flow` | strict | PASS |
| 实现库存扣减 | `backend.complex_business_logic` | `backend.complex_business_logic` | strict | PASS |
| 页面按钮的颜色改成蓝色 | `frontend.static_page_build` | `frontend.static_page_build` | light | PASS |
| 修复跨域鉴权错误 | `integration_debugging.cors_auth_debug` | `integration_debugging.cors_auth_debug` | strict | PASS |
| 线上Bug紧急修复 | `iteration.hotfix_workflow` | `iteration.hotfix_workflow` | strict | PASS |
| 编写测试计划 | `testing.test_plan` | `testing.test_plan` | standard | PASS |
| 我要做回归测试 | `testing.regression_test_suite` | `testing.regression_test_suite` | standard | PASS |
| 做一次安全审计 | `security.full_security_audit` | `security.full_security_audit` | strict | PASS |
| 用Docker部署 | `deployment_ops.docker_deploy` | `deployment_ops.docker_deploy` | strict | PASS |
| 生产监控方案 | `deployment_ops.production_monitoring` | `deployment_ops.production_monitoring` | strict | PASS |
| 生成环境变量样例 | `project_startup_docs.env_example_generator` | `project_startup_docs.env_example_generator` | standard | PASS |
| 项目结构规范 | `architecture.repo_structure_standard` | `architecture.repo_structure_standard` | standard | PASS |
| 分析代码质量问题 | `code_quality.code_review` | `code_quality.code_review` | standard | PASS |
| 实现列表筛选分页 | `frontend.list_search_pagination` | `frontend.list_search_pagination` | standard | PASS |
| 新建一个小程序配置文件 | `frontend.miniprogram_config_generator` | `frontend.miniprogram_config_generator` | standard | PASS |
| 规划下一版本 | `iteration.version_planning` | `iteration.version_planning` | standard | PASS |
| 解释支付系统是什么 | `backend.order_payment_flow` | `backend.order_payment_flow` | light | PASS |
