# V3.5：本地上下文检索、失败分类与可重复离线评测

> 定位：**离线、只读、可审查**的工程质量增强层；不包含向量数据库、完整 LSP 语义引擎、真实模型微调或无人值守编程。仍保留 V3.0–V3.4 的提案审批、测试授权、恢复与 Git/远程操作限制。

## 1. 搜索现有项目的候选上下文

```bash
python tools/context_retrieval.py --project examples/runnable-todo \
  --query "frontend css style" --limit 4
```

结果会包括相对路径、文件 SHA-256、匹配分数、行号和至多 5 行的短片段。相同文件和查询的结果可重复。此处采用词项与符号启发式评分，**并非深度语义理解**；不能保证找到真正需要修改的文件。只读取 UTF-8、32 KiB 以内的常见源码，排除软链接、`.ai`、`.git`、常见依赖/生成目录、凭据名称及疑似密钥文本。

文件大小、数量和字节数均有上限（默认最多扫描 3500 个文件，总计 16 MiB，单文件 32 KiB），超过限制会报错，不会静默读取无限内容。与完整源码索引不同，大型项目应先限定扫描范围，后续再使用显式路径。

## 2. 在 AI 提案阶段使用候选文件

```bash
# 仅本地预览 AI 将要使用哪些候选源文件：
python orchestrator/agent.py context --project examples/workflow-demo \
  --task-id EXAMPLE-35 --task "Change greet function punctuation" \
  --auto-context --auto-limit 3

# 使用审查过的文件白名单调用外部模型：
python orchestrator/agent.py context --project examples/workflow-demo \
  --task-id EXAMPLE-35 --task "Change greet function punctuation" \
  --include src/formatter.py
```

`--auto-context` **禁止与 `--send-to-model` 同时使用**。发给外部模型之前必须先查看建议，再逐个显式指定 `--include` 路径和其他原有网络授权选项。离线 `--response-file` 演示允许自动选择文件，但所有实际源码改动依然需要单独审批。

多轮修复可在 `loop.py start` 使用 `--auto-context`（仅离线响应），所选源文件会持久记录在该会话的原有本地状态中；后续修复复用已选白名单，不会悄悄加入新文件。

## 3. 根据失败类型选择修复检查方向

```bash
python tools/failure_triage.py --report /path/to/checks-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.json
```

支持依赖缺失、语法错误、断言失败、类型错误、连接失败、权限问题、超时和未知类型。分类是模式匹配，并不能证明根因。`orchestrator/agent.py --report` 会将分类和建议附于失败证据；多轮流程还会标记同一失败类别在先前轮次是否出现，提示检查已有补丁、环境与假设，而非无限重试同一种改法。

这**不会自动执行**依赖安装、提权、扩大超时、代码写入或任何测试。失败诊断文本属于不可信输入，模型也必须忽略其中可能夹带的指令。

## 4. 跨项目、可重复的质量评测

```bash
python tools/benchmark_v35.py --output benchmarks/v35_results.json
python tools/benchmark_v35.py --baseline benchmarks/v35_results.json
```

`benchmarks/v35_cases.json` 中固定了两个真实随包示例项目（`examples/workflow-demo`、`examples/runnable-todo`）的候选文件检索用例，以及固定错误文本分类用例。

报告含检索 Recall@K、Top-1 准确率、MRR@K、各项目命中数、失败分类准确率、基准文件 SHA-256。与旧报告比较时如基准文件指纹不同，将标为不可直接比较。它不执行源码、不联网，不会输出源码片段或原始诊断文本。

**重要：** 评测规模小、用例人工编排且同于开发调试用例，可能高估真实世界表现；本地 100% 只是这些样例全中，不能表述为“任意项目 100% 准确”，更不能等同真实 AI 修复成功率。若用于正式比较，需要增加独立盲测集、更多真实仓库和人工评估。

## 5. 安全与工程边界

- 自动检索只读，仍可能遗漏凭据检测规则未覆盖的敏感文本；发给外部模型前须人工审查全部文件。
- 文件匹配只依赖词项和浅层结构，跨语言符号推断不具备 LSP 的精确性。
- 失败分类与策略建议不会在未经审批情况下执行代码或将任务标为完成。
- Docker 测试在没有 Docker 的机器上不能证明真实隔离效果；请在具备容器运行时和适当配置的环境另行验证。
- 外部 GitHub 和大模型真实账号集成仍需在用户授权的环境中单独验证。
