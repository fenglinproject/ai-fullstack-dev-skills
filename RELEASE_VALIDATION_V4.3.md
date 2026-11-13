# V4.3 发布验证记录

## 真实执行的检查

| 验证项目 | 结果 | 边界 |
| --- | --- | --- |
| V4.3 18 项新测试 | 18/18 通过 | 独立进程运行 |
| 历史模块分组回归 | 285/285 通过 | 按模块、多个独立进程；不是单进程全量 |
| 所有 Python 工具及测试（合计） | 303/303 通过 | 包含上述分组，不重复计数 |
| V4.0 Smoke 工程验收 | 4/4 通过 | catalog、router、v4-unit、Todo API |
| 原有路由固定基准 | 28/28 技能、28/28 模式通过 | 固定小样本 |
| Todo API 测试 | 11/11 通过 | 随包可信示例 |
| Node.js / TypeScript / JS 语法 | 通过 | 随包样例及控制台文件 |
| 本地 Git 连续提交 | 5/5 提交，5/5 测试报告，5/5 任务验收 | 临时 Git 仓库，真实 Git 操作，非远程真实项目 |
| 144 个 Skill 目录审计 | 通过，0 issues | 静态引用与目录检查 |

分组测试统计：`test_orchestrator, test_workflow, test_workflow_demo, test_agent_bridge, test_loop, test_loop_cli, test_v21, test_v33` 共 121 项；`test_v34, test_v35, test_v36, test_v37` 共 85 项；`test_v38, test_v39, test_v40, test_v41, test_v42` 共 79 项；`test_v43` 共 18 项。各组每个模块独立运行；发现的 GitHub 旧状态适配问题已修复并复测通过。

## 遇到的超时

早期直接运行 `python -m unittest discover -s tests -v` 出现超时（输出停在旧版 V4.0 测试附近），**没有记为通过**。将新测试暂时纳入 Smoke 时，串行流程也发生超时，因此 V4.3 集成测试保留为 GitHub Actions 中的单独步骤；恢复后的四步 Smoke 单独通过。一次连续分组脚本超时，但此前已完成的模块结果有效，新模块再次独立验证通过。

## 未完成与限制

- 未在未知公开大型仓库上验证本地工作流或性能，也未进行生产环境长时间监控。
- 没有真实模型调用、线上 GitHub PR 创建或推送、Docker 容器执行。
- 本地报告哈希并非可信签名或防恶意管理员篡改机制；测试运行仍需要用户信任该项目。
- 历史 V4.2 清单不会自动迁移成 `committed`，避免错误归属提交。
