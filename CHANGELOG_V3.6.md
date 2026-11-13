# AI Fullstack Dev Skills V3.6 — 变更记录

## 代码能力

- 新增 `tools/ast_symbols.py`：本地 Python AST 类/函数/方法及名称级候选调用位置，限定扫描大小、数量与敏感路径，不执行项目代码。
- 新增 `tools/evidence_context.py`：从失败输出中提取已有项目文件的合法路径和行号线索，忽略外部绝对路径、路径穿越和不存在的文件；不读取/发送诊断指向的新源码。
- 新增 `tools/repair_context.py`：融合词项匹配、AST 符号和历史失败路径的只读上下文排序，带理由及得分；支持本地检查报告预览。
- `orchestrator/agent.py` 增加 `--symbol-hints`，并为失败报告生成安全的本地候选提示。模型源码白名单仍仅来自显式 `--include`，且保留 V3.5 的 `--auto-context` 远程发送限制。
- `orchestrator/loop.py` 的修复响应增加基于历史失败的候选文件预览。先校验所有已保存失败报告的哈希再生成新提案。

## 评测与质量

- 新增 `tools/benchmark_v36.py`、`benchmarks/v36_cases.json`、`tests/test_v36.py`。
- 新增两个不依赖外部包的合成多模块示例 `benchmarks/projects/inventory-service`、`benchmarks/projects/notes-workspace`，覆盖多个文件间的调用和测试。
- V3.6 固定评测区分可见 `dev`/`holdout` 子集及每项目结果，比较时校验测例 SHA-256 与 Top-K 配置。全部离线、只读。
- GitHub Actions 纳入 V3.6 固定基准、两个合成项目的 unittest、CI 审核报告；保留旧版所有门禁与 144 个 Skill。

## 明确不包含

完整 LSP/TypeScript 类型语义、向量数据库、外部模型实测、Docker 运行验证、无人工审批自动改代码、真正私密盲测或生产级修复成功率证明。
