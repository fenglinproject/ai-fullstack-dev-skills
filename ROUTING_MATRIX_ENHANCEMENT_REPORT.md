# 路由矩阵增强报告

生成日期：2026-07-01

本版本在“结构修复版”基础上完成第二轮增强，目标是让 Skills 从“目录可用”升级为“可路由、可门禁、可验证、可长期维护”。

## 本次完成

1. 新增 `skill_routing_matrix.json`：143 个 Skill 全部拥有路由 ID、阶段、阶段顺序、风险等级、执行模式、触发词、前置材料、输出产物、后续 Skill、禁止事项、工具适配、验证命令。
2. 新增 `SKILL_ROUTING_MATRIX.md`：人类可读路由矩阵总览。
3. 增强 `skills_index.json`：加入 `routing_matrix`、`stage_order`、`risk_level`、`execution_mode`、`must_not_do` 等字段。
4. 批量增强 143 个 `SKILL.md`：追加“路由矩阵增强：执行模式、反模式与验证”段落。
5. 新增 `CORE_SKILL_VIEW.md`：主 Skill + 子清单视图，不删除原 Skill，但降低选择成本。
6. 新增 `HARD_GATES.md`：支付、权限、数据库、部署、线上 Bug 等高风险场景强制门禁。
7. 新增 `START_HERE.md`：一键启动项目黄金路径。
8. 新增 `docs/00_getting_started/ai_tool_usage.md`：ChatGPT、Claude、Cursor、Windsurf、Codex、本地 IDE Agent 使用建议。
9. 新增 `templates/engineering/verification_commands.md`：Node、Vue/Vite、Python、Docker、数据库、API、安全验证命令模板。
10. 新增 `examples/` 示例项目骨架：todo-saas、order-payment、admin-crud、miniprogram-booking。
11. 新增 `tools/skill_quality_score.py` 和 `SKILL_QUALITY_REPORT.md`：Skill 质量评分器与报告。
12. 保留低破坏策略：未强制重命名 `05_backend`，而是在索引和路由矩阵中加入 `stage_order`。

## 推荐使用顺序

1. 先读 `START_HERE.md`
2. 再查 `skill_routing_matrix.json` 或 `SKILL_ROUTING_MATRIX.md`
3. 高风险任务先读 `HARD_GATES.md`
4. 开发/调试/部署任务参考 `templates/engineering/verification_commands.md`
5. 长期优化时运行 `python tools/skill_quality_score.py`

## 后续可继续优化

- 把 143 个 Skill 分批合并成 20～40 个高质量主 Skill。
- 给每个示例项目补充真正可运行的代码仓库。
- 根据实际技术栈生成更精确的验证命令和 CI 配置。
- 把路由矩阵接入 Agent 的自动选 Skill 逻辑。
