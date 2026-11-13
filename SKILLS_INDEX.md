# Skills Index

本索引由结构修复版重建，列出每个具体 Skill，便于人工查找和 AI 自动路由。

## 执行模式

| 模式 | 适用场景 | 文档要求 |
|---|---|---|
| 轻量模式 | 快速答疑、局部修改、小问题 | 不强制生成 docs |
| 标准模式 | 正常阶段推进 | 阶段结束时更新 docs |
| 严格模式 | 支付、权限、安全、上线、数据库变更、复杂 Bug | 必须输出文档、测试、风险、回滚、门禁 |

## 00_core：总控

路径：`skills/00_core`；Skill 数量：6。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 项目总控官 | `skills/00_core/00_project_orchestrator/SKILL.md` | 帮我做项目总控官；启动项目总控官 Skill；检查/生成/设计/拆分这个项目总控官 | 阶段路线图；当前阶段任务；风险清单 |
| 项目上下文收集 | `skills/00_core/01_project_context_collector/SKILL.md` | 帮我做项目上下文收集；启动项目上下文收集 Skill；检查/生成/设计/拆分这个项目上下文收集 | 项目上下文档案；假设列表；信息缺口 |
| 阶段门禁评审 | `skills/00_core/02_stage_gate_reviewer/SKILL.md` | 帮我做阶段门禁评审；启动阶段门禁评审 Skill；检查/生成/设计/拆分这个阶段门禁评审 | 通过/不通过结论；必须补齐项；建议优化项 |
| MVP 范围控制 | `skills/00_core/03_scope_controller/SKILL.md` | 帮我做MVP 范围控制；启动MVP 范围控制 Skill；检查/生成/设计/拆分这个MVP 范围控制 | 必须做；可延后；不建议做 |
| 需求变更管控 | `skills/00_core/04_change_request_manager/SKILL.md` | 帮我做需求变更管控；启动需求变更管控 Skill；检查/生成/设计/拆分这个需求变更管控 | 变更单；影响分析；工期影响 |
| 文档交付管理 | `skills/00_core/05_document_deliverable_manager/SKILL.md` | 帮我做文档交付管理；启动文档交付管理 Skill；检查/生成/设计/拆分这个文档交付管理 | 文档清单；缺失文档；文档模板 |

## 01_requirements：需求阶段

路径：`skills/01_requirements`；Skill 数量：11。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 想法转需求 | `skills/01_requirements/00_idea_to_requirements/SKILL.md` | 帮我做想法转需求；启动想法转需求 Skill；检查/生成/设计/拆分这个想法转需求 | 需求澄清结果；功能清单；业务流程 |
| 用户角色与权限分析 | `skills/01_requirements/01_user_role_permission_analysis/SKILL.md` | 帮我做用户角色与权限分析；启动用户角色与权限分析 Skill；检查/生成/设计/拆分这个用户角色与权限分析 | 角色表；权限矩阵；数据可见范围 |
| 业务流程梳理 | `skills/01_requirements/02_business_process_mapping/SKILL.md` | 帮我做业务流程梳理；启动业务流程梳理 Skill；检查/生成/设计/拆分这个业务流程梳理 | 主流程；分支流程；异常流程 |
| MVP 范围定义 | `skills/01_requirements/03_mvp_scope_definition/SKILL.md` | 帮我做MVP 范围定义；启动MVP 范围定义 Skill；检查/生成/设计/拆分这个MVP 范围定义 | MVP 功能；延后功能；删除功能 |
| PRD 生成 | `skills/01_requirements/04_prd_generator/SKILL.md` | 帮我做PRD 生成；启动PRD 生成 Skill；检查/生成/设计/拆分这个PRD  | PRD Markdown；页面清单；字段规则 |
| 页面功能说明 | `skills/01_requirements/05_page_function_spec/SKILL.md` | 帮我做页面功能说明；启动页面功能说明 Skill；检查/生成/设计/拆分这个页面功能说明 | 页面说明表；按钮说明表；跳转规则 |
| 业务规则定义 | `skills/01_requirements/06_business_rule_spec/SKILL.md` | 帮我做业务规则定义；启动业务规则定义 Skill；检查/生成/设计/拆分这个业务规则定义 | 规则编号；触发条件；处理逻辑 |
| 异常场景挖掘 | `skills/01_requirements/07_exception_scenario_mining/SKILL.md` | 帮我做异常场景挖掘；启动异常场景挖掘 Skill；检查/生成/设计/拆分这个异常场景挖掘 | 异常场景表；提示文案；前端处理 |
| 验收标准生成 | `skills/01_requirements/08_acceptance_criteria_builder/SKILL.md` | 帮我做验收标准生成；启动验收标准生成 Skill；检查/生成/设计/拆分这个验收标准 | 功能验收标准；接口验收标准；上线验收标准 |
| 需求评审 | `skills/01_requirements/09_requirements_review/SKILL.md` | 帮我做需求评审；启动需求评审 Skill；检查/生成/设计/拆分这个需求评审 | 问题清单；影响级别；修改建议 |
| 需求变更单 | `skills/01_requirements/10_requirement_change_order/SKILL.md` | 帮我做需求变更单；启动需求变更单 Skill；检查/生成/设计/拆分这个需求变更单 | 变更单；影响模块；工作量评估 |

## 02_product_design：产品设计阶段

路径：`skills/02_product_design`；Skill 数量：10。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 信息架构设计 | `skills/02_product_design/00_information_architecture/SKILL.md` | 帮我做信息架构设计；启动信息架构设计 Skill；检查/生成/设计/拆分这个信息架构 | 页面树；菜单结构；模块层级 |
| 用户流程设计 | `skills/02_product_design/01_user_flow_design/SKILL.md` | 帮我做用户流程设计；启动用户流程设计 Skill；检查/生成/设计/拆分这个用户流程 | 用户流程；关键节点；流失风险 |
| 低保真原型说明 | `skills/02_product_design/02_wireframe_spec/SKILL.md` | 帮我做低保真原型说明；启动低保真原型说明 Skill；检查/生成/设计/拆分这个低保真原型说明 | 低保真布局；模块说明；交互说明 |
| 交互状态设计 | `skills/02_product_design/03_interaction_state_spec/SKILL.md` | 帮我做交互状态设计；启动交互状态设计 Skill；检查/生成/设计/拆分这个交互状态 | 状态清单；触发条件；展示文案 |
| 表单设计规则 | `skills/02_product_design/04_form_design_rules/SKILL.md` | 帮我做表单设计规则；启动表单设计规则 Skill；检查/生成/设计/拆分这个表单规则 | 字段表；校验规则；错误提示 |
| 列表筛选分页设计 | `skills/02_product_design/05_list_filter_pagination_design/SKILL.md` | 帮我做列表筛选分页设计；启动列表筛选分页设计 Skill；检查/生成/设计/拆分这个列表筛选分页 | 列表字段表；筛选项；排序规则 |
| UI 风格规范 | `skills/02_product_design/06_ui_style_guide/SKILL.md` | 帮我做UI 风格规范；启动UI 风格规范 Skill；检查/生成/设计/拆分这个UI 风格规范 | 设计规范；组件样式；颜色字体 |
| 组件清单 | `skills/02_product_design/07_component_inventory/SKILL.md` | 帮我做组件清单；启动组件清单 Skill；检查/生成/设计/拆分这个组件清单 | 组件列表；属性设计；事件设计 |
| 提示文案设计 | `skills/02_product_design/08_microcopy_prompt_text/SKILL.md` | 帮我做提示文案设计；启动提示文案设计 Skill；检查/生成/设计/拆分这个提示文案 | 文案清单；触发场景；语气说明 |
| 设计评审 | `skills/02_product_design/09_design_review/SKILL.md` | 帮我做设计评审；启动设计评审 Skill；检查/生成/设计/拆分这个评审 | 设计问题表；开发风险；优化建议 |

## 03_architecture：技术架构阶段

路径：`skills/03_architecture`；Skill 数量：13。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 技术栈选型 | `skills/03_architecture/00_tech_stack_selection/SKILL.md` | 帮我做技术栈选型；启动技术栈选型 Skill；检查/生成/设计/拆分这个技术栈选型 | 推荐技术栈；替代方案；选型理由 |
| 前端 UI 组件库选型 | `skills/03_architecture/12_frontend_ui_library_selection/SKILL.md` | 推荐前端组件库；启动前端 UI 组件库选型 Skill；前端组件库怎么选 | 默认推荐；替代方案；安装与封装策略 |
| 整体架构方案 | `skills/03_architecture/01_architecture_blueprint/SKILL.md` | 帮我做整体架构方案；启动整体架构方案 Skill；检查/生成/设计/拆分这个整体架构方案 | 架构图文本；模块划分；数据流 |
| 项目目录结构规范 | `skills/03_architecture/02_repo_structure_standard/SKILL.md` | 帮我做项目目录结构规范；启动项目目录结构规范 Skill；检查/生成/设计/拆分这个项目目录结构规范 | 目录结构；命名规则；模块职责 |
| 环境规划 | `skills/03_architecture/03_environment_strategy/SKILL.md` | 帮我做环境规划；启动环境规划 Skill；检查/生成/设计/拆分这个环境规划 | 环境清单；变量表；初始化步骤 |
| 认证架构 | `skills/03_architecture/04_auth_architecture/SKILL.md` | 帮我做认证架构；启动认证架构 Skill；检查/生成/设计/拆分这个认证架构 | 认证流程；Token 策略；接口拦截 |
| 权限模型 | `skills/03_architecture/05_permission_model/SKILL.md` | 帮我做权限模型；启动权限模型 Skill；检查/生成/设计/拆分这个权限模型 | 权限模型；权限矩阵；数据范围规则 |
| 接口规范 | `skills/03_architecture/06_api_standard/SKILL.md` | 帮我做接口规范；启动接口规范 Skill；检查/生成/设计/拆分这个接口规范 | 接口规范；返回格式；错误码规范 |
| 异常处理规范 | `skills/03_architecture/07_error_handling_standard/SKILL.md` | 帮我做异常处理规范；启动异常处理规范 Skill；检查/生成/设计/拆分这个异常处理规范 | 错误分类；错误码；前端提示 |
| 日志与监控方案 | `skills/03_architecture/08_logging_monitoring_plan/SKILL.md` | 帮我做日志与监控方案；启动日志与监控方案 Skill；检查/生成/设计/拆分这个日志与监控方案 | 日志分类；字段规范；监控指标 |
| 缓存策略 | `skills/03_architecture/09_cache_strategy/SKILL.md` | 帮我做缓存策略；启动缓存策略 Skill；检查/生成/设计/拆分这个缓存策略 | 缓存对象；Key 设计；失效策略 |
| 第三方服务方案 | `skills/03_architecture/10_third_party_service_plan/SKILL.md` | 帮我做第三方服务方案；启动第三方服务方案 Skill；检查/生成/设计/拆分这个第三方服务方案 | 接入流程；配置项；回调处理 |
| 安全架构方案 | `skills/03_architecture/11_security_architecture/SKILL.md` | 帮我做安全架构方案；启动安全架构方案 Skill；检查/生成/设计/拆分这个安全架构方案 | 安全控制点；风险清单；防护方案 |

## 04_database：数据库阶段

路径：`skills/04_database`；Skill 数量：10。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 业务实体建模 | `skills/04_database/00_entity_modeling/SKILL.md` | 帮我做业务实体建模；启动业务实体建模 Skill；检查/生成/设计/拆分这个业务实体建模 | 实体清单；字段候选；实体关系 |
| 数据表设计 | `skills/04_database/01_table_design/SKILL.md` | 帮我做数据表设计；启动数据表设计 Skill；检查/生成/设计/拆分这个数据表 | 表结构；字段说明；建表 SQL |
| 表关系设计 | `skills/04_database/02_relationship_design/SKILL.md` | 帮我做表关系设计；启动表关系设计 Skill；检查/生成/设计/拆分这个表关系 | 关系图文本；关联字段；查询路径 |
| 索引设计 | `skills/04_database/03_index_design/SKILL.md` | 帮我做索引设计；启动索引设计 Skill；检查/生成/设计/拆分这个索引 | 索引清单；索引理由；慢查询风险 |
| 状态枚举设计 | `skills/04_database/04_status_enum_design/SKILL.md` | 帮我做状态枚举设计；启动状态枚举设计 Skill；检查/生成/设计/拆分这个状态枚举 | 状态枚举；状态机；允许操作 |
| 数据权限字段设计 | `skills/04_database/05_data_permission_scope/SKILL.md` | 帮我做数据权限字段设计；启动数据权限字段设计 Skill；检查/生成/设计/拆分这个数据权限字段 | scope 字段；查询限制；越权风险 |
| 迁移与初始化数据 | `skills/04_database/06_migration_seed_plan/SKILL.md` | 帮我做迁移与初始化数据；启动迁移与初始化数据 Skill；检查/生成/设计/拆分这个迁移与初始化数据 | 迁移顺序；种子数据；回滚策略 |
| 审计日志表设计 | `skills/04_database/07_audit_log_table_design/SKILL.md` | 帮我做审计日志表设计；启动审计日志表设计 Skill；检查/生成/设计/拆分这个审计日志表 | 日志表结构；记录字段；查询方式 |
| 备份与恢复设计 | `skills/04_database/08_backup_recovery_design/SKILL.md` | 帮我做备份与恢复设计；启动备份与恢复设计 Skill；检查/生成/设计/拆分这个备份与恢复 | 备份策略；恢复步骤；校验方式 |
| 单 SQL 生成器 | `skills/04_database/09_sql_generation/SKILL.md` | 生成 SQL；生成建表语句；设计数据库 |  |

## 05_api：接口设计阶段

路径：`skills/05_api`；Skill 数量：4。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 接口设计总控 | `skills/05_api/00_api_design_orchestrator/SKILL.md` | 生成接口文档；设计 API；生成 OpenAPI | 接口分组和端点清单；请求方法、路径、认证方式、权限要求；请求参数、响应结构、错误码 |
| OpenAPI 规范生成 | `skills/05_api/01_openapi_spec_generator/SKILL.md` | 生成接口文档；设计 API；生成 OpenAPI | 接口分组和端点清单；请求方法、路径、认证方式、权限要求；请求参数、响应结构、错误码 |
| 接口契约设计 | `skills/05_api/02_endpoint_contract_design/SKILL.md` | 生成接口文档；设计 API；生成 OpenAPI | 接口分组和端点清单；请求方法、路径、认证方式、权限要求；请求参数、响应结构、错误码 |
| 接口 Mock 与校验 | `skills/05_api/03_api_mock_validation/SKILL.md` | 生成接口文档；设计 API；生成 OpenAPI | 接口分组和端点清单；请求方法、路径、认证方式、权限要求；请求参数、响应结构、错误码 |

## 05_backend：后端开发阶段

路径：`skills/05_backend`；Skill 数量：13。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 后端项目初始化 | `skills/05_backend/00_backend_project_init/SKILL.md` | 帮我做后端项目初始化；启动后端项目初始化 Skill；检查/生成/设计/拆分这个后端项目初始化 | 初始化步骤；目录结构；基础配置 |
| 统一返回体与异常处理 | `skills/05_backend/01_unified_response_exception/SKILL.md` | 帮我做统一返回体与异常处理；启动统一返回体与异常处理 Skill；检查/生成/设计/拆分这个统一返回体与异常处理 | 返回体代码；异常类；拦截器 |
| 登录注册模块 | `skills/05_backend/02_auth_login_register/SKILL.md` | 帮我做登录注册模块；启动登录注册模块 Skill；检查/生成/设计/拆分这个登录注册模块 | 接口代码；参数校验；Token 逻辑 |
| RBAC 角色权限菜单 | `skills/05_backend/03_rbac_role_menu/SKILL.md` | 帮我做RBAC 角色权限菜单；启动RBAC 角色权限菜单 Skill；检查/生成/设计/拆分这个RBAC 角色权限菜单 | 表结构映射；接口；拦截器 |
| 业务 CRUD 模块 | `skills/05_backend/04_crud_module_generator/SKILL.md` | 帮我做业务 CRUD 模块；启动业务 CRUD 模块 Skill；检查/生成/设计/拆分这个业务 CRUD 模块 | CRUD 代码；参数校验；分页搜索 |
| 复杂业务逻辑 | `skills/05_backend/05_complex_business_logic/SKILL.md` | 帮我做复杂业务逻辑；启动复杂业务逻辑 Skill；检查/生成/设计/拆分这个复杂业务逻辑 | 流程代码；事务边界；异常处理 |
| 订单支付流程 | `skills/05_backend/06_order_payment_flow/SKILL.md` | 帮我做订单支付流程；启动订单支付流程 Skill；检查/生成/设计/拆分这个订单支付流程 | 订单流程；支付接口；回调处理 |
| 文件上传与存储 | `skills/05_backend/07_file_upload_storage/SKILL.md` | 帮我做文件上传与存储；启动文件上传与存储 Skill；检查/生成/设计/拆分这个文件上传与存储 | 上传接口；校验逻辑；存储路径 |
| 回调与 Webhook 处理 | `skills/05_backend/08_callback_webhook_handler/SKILL.md` | 帮我做回调与 Webhook 处理；启动回调与 Webhook 处理 Skill；检查/生成/设计/拆分这个回调与 Webhook 处理 | 验签逻辑；幂等逻辑；重试策略 |
| 定时任务 | `skills/05_backend/09_scheduler_job/SKILL.md` | 帮我做定时任务；启动定时任务 Skill；检查/生成/设计/拆分这个定时任务 | 任务列表；执行频率；并发控制 |
| Redis 缓存与限流 | `skills/05_backend/10_redis_cache_rate_limit/SKILL.md` | 帮我做Redis 缓存与限流；启动Redis 缓存与限流 Skill；检查/生成/设计/拆分这个Redis 缓存与限流 | Key 设计；代码；过期策略 |
| 事务与幂等 | `skills/05_backend/11_transaction_idempotency/SKILL.md` | 帮我做事务与幂等；启动事务与幂等 Skill；检查/生成/设计/拆分这个事务与幂等 | 事务边界；幂等 Key；锁策略 |
| 后端自测 | `skills/05_backend/12_backend_self_test/SKILL.md` | 帮我做后端自测；启动后端自测 Skill；检查/生成/设计/拆分这个后端自测 | 自测清单；curl 示例；边界用例 |

## 06_frontend：前端开发阶段

路径：`skills/06_frontend`；Skill 数量：13。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 前端项目初始化 | `skills/06_frontend/00_frontend_project_init/SKILL.md` | 帮我做前端项目初始化；启动前端项目初始化 Skill；检查/生成/设计/拆分这个前端项目初始化 | 初始化步骤；目录结构；基础封装 |
| 前端项目初始化文件生成器 | `skills/06_frontend/01_frontend_project_scaffold/SKILL.md` | 初始化前端项目；生成小程序前端；生成 uni-app 项目 |  |
| 小程序配置文件生成器 | `skills/06_frontend/02_miniprogram_config_generator/SKILL.md` |  |  |
| 路由守卫与权限控制 | `skills/06_frontend/03_route_guard_permission/SKILL.md` | 帮我做路由守卫与权限控制；启动路由守卫与权限控制 Skill；检查/生成/设计/拆分这个路由守卫与权限控制 | 路由配置；守卫逻辑；权限指令 |
| 状态管理 | `skills/06_frontend/04_state_management/SKILL.md` | 帮我做状态管理；启动状态管理 Skill；检查/生成/设计/拆分这个状态管理 | Store 结构；状态字段；Action |
| 接口请求封装 | `skills/06_frontend/05_api_client_wrapper/SKILL.md` | 帮我做接口请求封装；启动接口请求封装 Skill；检查/生成/设计/拆分这个接口请求封装 | 请求封装代码；拦截器；错误提示 |
| 基础组件封装 | `skills/06_frontend/06_base_components/SKILL.md` | 帮我做基础组件封装；启动基础组件封装 Skill；检查/生成/设计/拆分这个基础组件封装 | 组件清单；Props；Events |
| 静态页面搭建 | `skills/06_frontend/07_static_page_build/SKILL.md` | 帮我做静态页面搭建；启动静态页面搭建 Skill；检查/生成/设计/拆分这个静态页面搭建 | 页面代码；组件拆分；样式说明 |
| 表单校验与提交 | `skills/06_frontend/08_form_validation_submit/SKILL.md` | 帮我做表单校验与提交；启动表单校验与提交 Skill；检查/生成/设计/拆分这个表单校验与提交 | 表单代码；校验规则；提交流程 |
| 列表搜索筛选分页 | `skills/06_frontend/09_list_search_pagination/SKILL.md` | 帮我做列表搜索筛选分页；启动列表搜索筛选分页 Skill；检查/生成/设计/拆分这个列表搜索筛选分页 | 页面代码；查询参数；分页逻辑 |
| 空/加载/错误状态处理 | `skills/06_frontend/10_error_empty_loading_states/SKILL.md` | 帮我做空/加载/错误状态处理；启动空/加载/错误状态处理 Skill；检查/生成/设计/拆分这个空/加载/错误状态处理 | 状态组件；触发条件；提示文案 |
| 多端适配 | `skills/06_frontend/11_mobile_pc_adaptation/SKILL.md` | 帮我做多端适配；启动多端适配 Skill；检查/生成/设计/拆分这个多端适配 | 适配策略；断点规则；兼容清单 |
| 前端自测 | `skills/06_frontend/12_frontend_self_test/SKILL.md` | 帮我做前端自测；启动前端自测 Skill；检查/生成/设计/拆分这个前端自测 | 自测表；问题记录模板；回归点 |

## 07_integration_debugging：联调与排错

路径：`skills/07_integration_debugging`；Skill 数量：9。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 接口联调计划 | `skills/07_integration_debugging/00_api_integration_plan/SKILL.md` | 帮我做接口联调计划；启动接口联调计划 Skill；检查/生成/设计/拆分这个接口联调计划 | 联调顺序；依赖关系；Mock 策略 |
| 网络请求错误排查 | `skills/07_integration_debugging/01_network_error_debug/SKILL.md` | 帮我做网络请求错误排查；启动网络请求错误排查 Skill；检查/生成/设计/拆分这个网络请求错误排查 | 原因排序；排查步骤；修复建议 |
| 跨域与鉴权排查 | `skills/07_integration_debugging/02_cors_auth_debug/SKILL.md` | 帮我做跨域与鉴权排查；启动跨域与鉴权排查 Skill；检查/生成/设计/拆分这个跨域与鉴权排查 | 问题定位；配置修改；验证步骤 |
| 数据不一致排查 | `skills/07_integration_debugging/03_data_mismatch_debug/SKILL.md` | 帮我做数据不一致排查；启动数据不一致排查 Skill；检查/生成/设计/拆分这个数据不一致排查 | 差异表；修改方案；兼容建议 |
| 支付回调排查 | `skills/07_integration_debugging/04_payment_callback_debug/SKILL.md` | 帮我做支付回调排查；启动支付回调排查 Skill；检查/生成/设计/拆分这个支付回调排查 | 排查链路；原因分析；修复方案 |
| 完整业务流程跑通 | `skills/07_integration_debugging/05_full_process_runthrough/SKILL.md` | 帮我做完整业务流程跑通；启动完整业务流程跑通 Skill；检查/生成/设计/拆分这个完整业务流程跑通 | 流程清单；卡点记录；修复优先级 |
| Bug 根因分析 | `skills/07_integration_debugging/06_bug_root_cause_analysis/SKILL.md` | 帮我做Bug 根因分析；启动Bug 根因分析 Skill；检查/生成/设计/拆分这个Bug 根因分析 | 根因分析；修复方案；影响面 |
| 修复后回归 | `skills/07_integration_debugging/07_regression_after_fix/SKILL.md` | 帮我做修复后回归；启动修复后回归 Skill；检查/生成/设计/拆分这个修复后回归 | 回归清单；验证结果；风险提醒 |
| 系统性调试 | `skills/07_integration_debugging/08_systematic_debugging/SKILL.md` | 帮我系统性调试；不要乱改，按步骤排查；这个报错怎么定位 | 调试问题单；复现方案；问题边界判断：前端 / 后端 / 数据库 / 第三方 / 环境 / 部署 / 数据 |

## 08_testing：测试阶段

路径：`skills/08_testing`；Skill 数量：11。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 测试计划 | `skills/08_testing/00_test_plan/SKILL.md` | 帮我做测试计划；启动测试计划 Skill；检查/生成/设计/拆分这个测试计划 | 测试计划；范围清单；风险区域 |
| 功能测试用例 | `skills/08_testing/01_functional_test_cases/SKILL.md` | 帮我做功能测试用例；启动功能测试用例 Skill；检查/生成/设计/拆分这个功能测试用例 | 测试用例表；步骤；预期结果 |
| 边界与异常用例 | `skills/08_testing/02_boundary_exception_cases/SKILL.md` | 帮我做边界与异常用例；启动边界与异常用例 Skill；检查/生成/设计/拆分这个边界与异常用例 | 边界用例；异常用例；错误提示检查 |
| 权限测试用例 | `skills/08_testing/03_permission_test_cases/SKILL.md` | 帮我做权限测试用例；启动权限测试用例 Skill；检查/生成/设计/拆分这个权限测试用例 | 权限用例；越权用例；预期拒绝结果 |
| 接口测试用例 | `skills/08_testing/04_api_test_cases/SKILL.md` | 帮我做接口测试用例；启动接口测试用例 Skill；检查/生成/设计/拆分这个接口测试用例 | 接口用例；curl/Postman 示例；断言 |
| 兼容性测试 | `skills/08_testing/05_compatibility_test_cases/SKILL.md` | 帮我做兼容性测试；启动兼容性测试 Skill；检查/生成/设计/拆分这个兼容性测试 | 兼容矩阵；测试步骤；问题记录模板 |
| 性能测试计划 | `skills/08_testing/06_performance_test_plan/SKILL.md` | 帮我做性能测试计划；启动性能测试计划 Skill；检查/生成/设计/拆分这个性能测试计划 | 性能指标；测试方法；优化建议 |
| Bug 报告模板 | `skills/08_testing/07_bug_report_template/SKILL.md` | 帮我做Bug 报告模板；启动Bug 报告模板 Skill；检查/生成/设计/拆分这个Bug 报告模板 | Bug 报告；严重级别；责任模块 |
| 回归测试套件 | `skills/08_testing/08_regression_test_suite/SKILL.md` | 帮我做回归测试套件；启动回归测试套件 Skill；检查/生成/设计/拆分这个回归测试套件 | 回归范围；用例清单；通过标准 |
| 上线验收测试 | `skills/08_testing/09_release_acceptance_test/SKILL.md` | 帮我做上线验收测试；启动上线验收测试 Skill；检查/生成/设计/拆分这个上线验收测试 | 上线验收清单；阻塞项；上线结论 |
| 测试驱动开发（TDD） | `skills/08_testing/10_test_driven_development/SKILL.md` | 我要测试驱动开发；按 TDD 做这个功能；先写测试再写代码 | TDD 任务卡；测试清单：单元测试 / 接口测试 / 集成测试 / E2E 测试的取舍；红灯阶段：应先失败的测试 |

## 09_security：安全阶段

路径：`skills/09_security`；Skill 数量：14。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 项目全量安全检查 | `skills/09_security/00_full_security_audit/SKILL.md` | 帮我做项目全量安全检查；启动项目全量安全检查 Skill；检查/生成/设计/拆分这个项目全量安全 | 安全等级；风险清单；必须修复项 |
| 登录注册安全检查 | `skills/09_security/01_auth_security_check/SKILL.md` | 帮我做登录注册安全检查；启动登录注册安全检查 Skill；检查/生成/设计/拆分这个登录注册安全 | 认证风险；修复方案；测试用例 |
| Token 与会话安全 | `skills/09_security/02_token_session_security/SKILL.md` | 帮我做Token 与会话安全；启动Token 与会话安全 Skill；检查/生成/设计/拆分这个Token 与会话安全 | Token 风险；改造建议；验证步骤 |
| 权限与越权检查 | `skills/09_security/03_rbac_overpermission_check/SKILL.md` | 帮我做权限与越权检查；启动权限与越权检查 Skill；检查/生成/设计/拆分这个权限与越权 | 越权风险；接口风险表；修复建议 |
| SQL 注入检查 | `skills/09_security/04_sql_injection_check/SKILL.md` | 帮我做SQL 注入检查；启动SQL 注入检查 Skill；检查/生成/设计/拆分这个SQL 注入 | 注入风险；白名单方案；参数化改造 |
| XSS 与 CSRF 检查 | `skills/09_security/05_xss_csrf_check/SKILL.md` | 帮我做XSS 与 CSRF 检查；启动XSS 与 CSRF 检查 Skill；检查/生成/设计/拆分这个XSS 与 CSRF  | XSS/CSRF 风险；过滤策略；CSP/SameSite 建议 |
| 防刷与幂等安全 | `skills/09_security/06_rate_limit_idempotency_check/SKILL.md` | 帮我做防刷与幂等安全；启动防刷与幂等安全 Skill；检查/生成/设计/拆分这个防刷与幂等安全 | 限流规则；幂等方案；高危接口表 |
| 文件上传安全检查 | `skills/09_security/07_upload_security_check/SKILL.md` | 帮我做文件上传安全检查；启动文件上传安全检查 Skill；检查/生成/设计/拆分这个文件上传安全 | 上传风险；白名单；存储隔离 |
| 敏感数据安全检查 | `skills/09_security/08_sensitive_data_check/SKILL.md` | 帮我做敏感数据安全检查；启动敏感数据安全检查 Skill；检查/生成/设计/拆分这个敏感数据安全 | 敏感信息风险；脱敏方案；密钥管理建议 |
| 支付与回调安全检查 | `skills/09_security/09_payment_security_check/SKILL.md` | 帮我做支付与回调安全检查；启动支付与回调安全检查 Skill；检查/生成/设计/拆分这个支付与回调安全 | 支付风险；状态机修复；对账策略 |
| 后台管理安全检查 | `skills/09_security/10_admin_panel_security_check/SKILL.md` | 帮我做后台管理安全检查；启动后台管理安全检查 Skill；检查/生成/设计/拆分这个后台管理安全 | 后台风险；权限改造；审计建议 |
| 部署与服务器安全检查 | `skills/09_security/11_deploy_server_security_check/SKILL.md` | 帮我做部署与服务器安全检查；启动部署与服务器安全检查 Skill；检查/生成/设计/拆分这个部署与服务器安全 | 部署风险；加固步骤；验证命令 |
| 日志与错误安全检查 | `skills/09_security/12_log_error_security_check/SKILL.md` | 帮我做日志与错误安全检查；启动日志与错误安全检查 Skill；检查/生成/设计/拆分这个日志与错误安全 | 泄露风险；统一错误方案；日志脱敏规则 |
| 上线安全门禁 | `skills/09_security/13_security_acceptance_gate/SKILL.md` | 帮我做上线安全门禁；启动上线安全门禁 Skill；检查/生成/设计/拆分这个上线安全门禁 | 上线结论；阻塞项；可延后项 |

## 10_deployment_ops：部署运维阶段

路径：`skills/10_deployment_ops`；Skill 数量：11。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 服务器准备 | `skills/10_deployment_ops/00_server_prepare/SKILL.md` | 帮我做服务器准备；启动服务器准备 Skill；检查/生成/设计/拆分这个服务器准备 | 服务器初始化步骤；目录规划；权限建议 |
| 环境变量配置 | `skills/10_deployment_ops/01_env_variables_config/SKILL.md` | 帮我做环境变量配置；启动环境变量配置 Skill；检查/生成/设计/拆分这个环境变量配置 | 变量表；配置示例；安全注意 |
| 域名 SSL Nginx | `skills/10_deployment_ops/02_nginx_ssl_domain/SKILL.md` | 帮我做域名 SSL Nginx；启动域名 SSL Nginx Skill；检查/生成/设计/拆分这个域名 SSL Nginx | Nginx 配置；SSL 步骤；验证方法 |
| 前端打包部署 | `skills/10_deployment_ops/03_frontend_deploy/SKILL.md` | 帮我做前端打包部署；启动前端打包部署 Skill；检查/生成/设计/拆分这个前端打包部署 | 打包命令；部署步骤；缓存配置 |
| 后端打包部署 | `skills/10_deployment_ops/04_backend_deploy/SKILL.md` | 帮我做后端打包部署；启动后端打包部署 Skill；检查/生成/设计/拆分这个后端打包部署 | 部署命令；进程守护；日志路径 |
| Docker 部署 | `skills/10_deployment_ops/05_docker_deploy/SKILL.md` | 帮我做Docker 部署；启动Docker 部署 Skill；检查/生成/设计/拆分这个Docker 部署 | Dockerfile；compose.yml；变量配置 |
| 数据库初始化与备份 | `skills/10_deployment_ops/06_database_init_backup/SKILL.md` | 帮我做数据库初始化与备份；启动数据库初始化与备份 Skill；检查/生成/设计/拆分这个数据库初始化与备份 | 初始化步骤；备份脚本；恢复步骤 |
| 灰度上线 | `skills/10_deployment_ops/07_gray_release/SKILL.md` | 帮我做灰度上线；启动灰度上线 Skill；检查/生成/设计/拆分这个灰度上线 | 灰度步骤；观察指标；回滚触发条件 |
| 回滚方案 | `skills/10_deployment_ops/08_rollback_plan/SKILL.md` | 帮我做回滚方案；启动回滚方案 Skill；检查/生成/设计/拆分这个回滚方案 | 回滚步骤；回滚风险；演练清单 |
| 生产监控 | `skills/10_deployment_ops/09_production_monitoring/SKILL.md` | 帮我做生产监控；启动生产监控 Skill；检查/生成/设计/拆分这个生产监控 | 监控清单；告警阈值；排查路径 |
| 运维手册 | `skills/10_deployment_ops/10_operation_runbook/SKILL.md` | 帮我做运维手册；启动运维手册 Skill；检查/生成/设计/拆分这个运维手册 | 运维手册；故障处理 SOP；联系人/账号清单 |

## 11_iteration：迭代阶段

路径：`skills/11_iteration`；Skill 数量：6。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 用户反馈归类 | `skills/11_iteration/00_feedback_triage/SKILL.md` | 帮我做用户反馈归类；启动用户反馈归类 Skill；检查/生成/设计/拆分这个用户反馈归类 | 反馈分类；优先级；处理建议 |
| 版本规划 | `skills/11_iteration/01_version_planning/SKILL.md` | 帮我做版本规划；启动版本规划 Skill；检查/生成/设计/拆分这个版本规划 | 版本目标；需求清单；排期 |
| 线上紧急修复 | `skills/11_iteration/02_hotfix_workflow/SKILL.md` | 帮我做线上紧急修复；启动线上紧急修复 Skill；检查/生成/设计/拆分这个线上紧急修复 | 应急步骤；修复方案；发布步骤 |
| 需求池维护 | `skills/11_iteration/03_backlog_grooming/SKILL.md` | 帮我做需求池维护；启动需求池维护 Skill；检查/生成/设计/拆分这个需求池维护 | 需求排序；保留/删除/延后；下一步 |
| 版本发布说明 | `skills/11_iteration/04_release_notes/SKILL.md` | 帮我做版本发布说明；启动版本发布说明 Skill；检查/生成/设计/拆分这个版本发布说明 | 用户版说明；内部版说明；风险提示 |
| 交付文档沉淀 | `skills/11_iteration/05_handover_docs/SKILL.md` | 帮我做交付文档沉淀；启动交付文档沉淀 Skill；检查/生成/设计/拆分这个交付文档沉淀 | 交付清单；缺失项；文档模板 |

## 12_code_quality：代码质量

路径：`skills/12_code_quality`；Skill 数量：6。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 代码审查 | `skills/12_code_quality/00_code_review/SKILL.md` | 帮我做代码审查；启动代码审查 Skill；检查/生成/设计/拆分这个代码审查 | 问题清单；必须修改；建议优化 |
| 重构计划 | `skills/12_code_quality/01_refactoring_plan/SKILL.md` | 帮我做重构计划；启动重构计划 Skill；检查/生成/设计/拆分这个重构计划 | 重构目标；步骤；风险 |
| Git 分支提交规范 | `skills/12_code_quality/02_git_branch_commit/SKILL.md` | 帮我做Git 分支提交规范；启动Git 分支提交规范 Skill；检查/生成/设计/拆分这个Git 分支提交规范 | 分支规范；commit 模板；合并流程 |
| 依赖升级检查 | `skills/12_code_quality/03_dependency_upgrade/SKILL.md` | 帮我做依赖升级检查；启动依赖升级检查 Skill；检查/生成/设计/拆分这个依赖升级 | 升级建议；风险；测试点 |
| 性能优化 | `skills/12_code_quality/04_performance_optimization/SKILL.md` | 帮我做性能优化；启动性能优化 Skill；检查/生成/设计/拆分这个性能优化 | 瓶颈定位；优化方案；验证指标 |
| 可观测性与日志规范 | `skills/12_code_quality/05_observability_logs/SKILL.md` | 帮我做可观测性与日志规范；启动可观测性与日志规范 Skill；检查/生成/设计/拆分这个可观测性与日志规范 | 日志字段；链路追踪；审计规范 |

## 13_documentation：docs 文档生成

路径：`skills/13_documentation`；Skill 数量：4。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| docs 文档总控生成器 | `skills/13_documentation/00_docs_orchestrator/SKILL.md` | 生成项目文档；文档放到 docs 里面；生成 docs |  |
| 阶段文档生成器 | `skills/13_documentation/01_stage_doc_generator/SKILL.md` |  |  |
| docs/README.md 文档索引生成器 | `skills/13_documentation/02_docs_index_generator/SKILL.md` |  |  |
| 文档质量检查门禁 | `skills/13_documentation/03_doc_review_gate/SKILL.md` |  |  |

## 14_project_startup_docs：具体业务项目启动文档

路径：`skills/14_project_startup_docs`；Skill 数量：3。

| Skill | 路径 | 触发词示例 | 标准输出摘要 |
|---|---|---|---|
| 具体业务项目启动文档生成器 | `skills/14_project_startup_docs/00_project_startup_docs_generator/SKILL.md` | 生成启动文档；项目怎么启动；用编译器怎么启动 |  |
| .env.example 生成器 | `skills/14_project_startup_docs/01_env_example_generator/SKILL.md` |  |  |
| docs/00_getting_started 文档生成器 | `skills/14_project_startup_docs/02_getting_started_docs_generator/SKILL.md` |  |  |
