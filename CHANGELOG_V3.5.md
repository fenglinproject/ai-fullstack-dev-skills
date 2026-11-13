# AI Fullstack Dev Skills V3.5 — 变更记录

## 新增

- `tools/context_retrieval.py`：有界 UTF-8 源码检索，返回候选路径/行号/指纹，排除软链接和常见密钥文件，不访问网络。
- `tools/failure_triage.py`：对实际失败诊断进行启发式分类，给出谨慎的排查建议；重复类别触发复核提示。
- `tools/benchmark_v35.py` 和 `benchmarks/v35_cases.json`：跨两个随包项目的固定离线基准、按项目统计、与基线比较、报告指纹。
- `tests/test_v35.py`：安全边界、确定性、检索、失败分类、模型发送限制和原有循环接入回归。
- `docs/ENGINEERING_V3.5.md`：使用说明、风险和能力边界。

## 集成和兼容性

- `orchestrator/agent.py` 支持 `--auto-context --auto-limit`，用于本地候选预览和离线提案；严禁与外部 `--send-to-model` 组合，必须显式指定 `--include` 后才能发送源码。
- `orchestrator/agent.py` 的失败报告上下文含修复分类和建议。
- `orchestrator/loop.py start` 支持离线自动选择文件；测试失败后的下一轮优先参考失败分类和类别重复情况。旧调用方式和人工审批流程保持有效。
- CI 新增 V3.5 固定评测门槛，并保留所有既有测试。

## 明确不包含

- 无向量嵌入/LSP 级语义索引、无人值守修改、自动部署、自动安装依赖、自动扩容超时、模型质量保证或真实外部服务验证。
- V3.5 离线基准数值只能反映固定样例集，不能作为广泛项目成功率估计。
