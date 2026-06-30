# 07_integration_debugging Skills

本目录包含以下细粒度 Skill：

- [接口联调计划](./00_api_integration_plan/SKILL.md)：按模块规划前后端接口联调顺序和依赖
- [网络请求错误排查](./01_network_error_debug/SKILL.md)：排查 404/500/超时/参数错误/返回结构不一致
- [跨域与鉴权排查](./02_cors_auth_debug/SKILL.md)：排查 CORS、Token 丢失、Cookie、Header、权限拦截问题
- [数据不一致排查](./03_data_mismatch_debug/SKILL.md)：排查字段名不一致、类型错误、分页错、状态枚举错
- [支付回调排查](./04_payment_callback_debug/SKILL.md)：排查支付成功但订单未更新、重复回调、验签失败
- [完整业务流程跑通](./05_full_process_runthrough/SKILL.md)：把注册/登录/下单/支付/后台处理等主流程完整跑通
- [Bug 根因分析](./06_bug_root_cause_analysis/SKILL.md)：不只修表面问题，找出根因、影响面和防复发措施
- [修复后回归](./07_regression_after_fix/SKILL.md)：修复 bug 后检查相关功能是否被影响