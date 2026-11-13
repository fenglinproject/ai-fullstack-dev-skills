# AI 工具适配说明

不同 AI 工具适合不同阶段。不要让纯对话工具承担完整仓库修改，也不要让代码 Agent 在需求不清时直接写代码。

| 工具 | 更适合 | 不适合 |
|---|---|---|
| ChatGPT | 需求澄清、PRD、架构、数据库/API 设计、代码片段、审查清单 | 大量文件级重构、持续跑测试 |
| Claude | 长文档分析、复杂需求梳理、重构方案、对比评审 | 需要频繁终端执行的任务 |
| Cursor / Windsurf | 直接修改项目文件、跨文件实现、前后端联调 | 没有明确需求和验收标准时直接开写 |
| Codex / 本地 IDE Agent | 执行测试、修 Bug、跑命令、代码库内改动、CI 问题排查 | 单纯产品讨论或模糊需求 |
| 纯聊天窗口 | 方案设计、模板生成、检查清单、代码审查建议 | 需要真实验证“项目已通过测试”的任务 |

## 每个 Skill 的工具适配字段

`skills_index.json` 和 `skill_routing_matrix.json` 中每个 Skill 增加：

```json
{
  "tool_adaptation": {
    "conversation_only": true,
    "repo_context_recommended": false,
    "terminal_recommended": false,
    "file_write_recommended": true
  }
}
```

含义：

- `conversation_only`：适合纯对话完成。
- `repo_context_recommended`：最好在真实代码仓库中执行。
- `terminal_recommended`：建议能运行命令、测试、构建。
- `file_write_recommended`：建议允许 AI 写入或修改文件。

## 使用原则

1. 需求/设计/架构阶段可以纯对话。
2. 后端、前端、测试、部署、调试阶段最好在代码仓库中执行。
3. 高风险任务必须能验证，不能只靠文字承诺。
4. AI 如果不能跑命令，必须明确说明“未实际验证”。
