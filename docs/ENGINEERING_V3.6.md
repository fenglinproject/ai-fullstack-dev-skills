# V3.6 — Python AST 符号检索、历史失败证据与扩展离线评测

> 目标：在 **不修改代码、不运行代码、不调用外部模型** 的前提下，提高项目内相关文件的定位能力。保留 V3.0–V3.5 的独立审批、测试授权和回退机制。所有搜索结果都是候选线索，并不证明运行时调用关系或真实故障原因。

## 1. Python AST 符号和调用位置

```bash
python tools/ast_symbols.py --project benchmarks/projects/inventory-service --query OrderService.place_order --limit 5
python tools/ast_symbols.py --project benchmarks/projects/notes-workspace --query NoteStore.save_note --no-references
```

返回模块相对路径、类/方法/函数的限定名、起止行号、名称匹配分数，以及至多 20 个名称相同的候选调用位置（不是精确引用）。只使用 Python 标准库 `ast`；不支持 TS/JS 的语义解析，不进行 LSP 类型推断、运行期绑定解析，也不执行源码。源码按 V3.5 的安全过滤和扫描上限读取，自动跳过过大的文件、软链接、常见凭据文件和疑似含密钥的文件，语法不正确的 Python 文件会出现在 `parse_errors`。

与 V3.4 `semantic_impact.py` 的差别：该工具用于定位 **当前工作树** 中的定义和候选调用位置，不依赖 Git HEAD；V3.4 侧重 Git 基线的改动前后差异及候选影响范围。

## 2. 基于失败日志的上下文建议

```bash
# 对纯文本日志，只从已存在的项目文件中提取路径线索
python tools/evidence_context.py --project benchmarks/projects/inventory-service --diagnostic-file /path/to/test-log.txt

# 多轮失败后，可针对项目 .ai/reports 下的已执行报告预览建议（名称来自真正的检查流程）
python tools/repair_context.py --project project --task "Fix order total assertion" \
  --report checks-0123456789abcdef0123456789abcdef.json
```

`repair_context` 合并三个信号：原有词项检索、Python AST 符号检索和被验证为现有项目文件的测试日志路径。多轮出现相同路径会增加其排序权重。输出 `evidence` 字段说明为什么推荐该文件；**不会把这些文件直接添加到给外部模型的源码白名单**。日志和代码均属于不可信文本；报告字段 `actually_executed` 只表示工具的报告声明，不能单独防范被本地攻击者伪造的报告。V3.2 多轮修复仍会校验持久保存的报告哈希。

在 AI 代理里，本地预览：

```bash
python orchestrator/agent.py context --project examples/workflow-demo \
  --task-id HINTS36 --task "Change greet function punctuation" \
  --include src/formatter.py --symbol-hints
```

如果有失败报告，`agent.py context` 的输出会带 `repair_context_hints`，实际 `build_context` 只加入显式 `--include` 文件中被验证的 `file_hints`。要发送新的源码给外部模型，仍须明确审查后传入 `--include`。`--symbol-hints` 只增添返回给本地用户的元数据，不自动扩大模型可访问范围。

## 3. 扩展评测

```bash
python tools/benchmark_v36.py --output benchmarks/v36_results.json --min-holdout 0.75
python tools/benchmark_v36.py --baseline benchmarks/v36_results.json

# 两个新增合成项目的可执行 smoke tests（stdlib-only）
(cd benchmarks/projects/inventory-service && python -m unittest discover -s tests)
(cd benchmarks/projects/notes-workspace && python -m unittest discover -s tests)
```

包含四个随包项目：原有 `workflow-demo`、`runnable-todo` 和两个新建的 **合成示例** `inventory-service`、`notes-workspace`。固定 14 个符号用例、8 个追踪路径用例（包含不存在的符号、外部路径、路径穿越和无关日志）。`dev` 与 `holdout` 是 **可见的预先标注切片**，仅用于在固定用例之间分组检查；不是未见过的私密盲测数据，也不能证明在真实大型生产项目中达到同样效果。

报告包括指标分组、项目维度结果、SHA-256 测例指纹、Top-1 和 Top-K。基线与当前的用例指纹或 `top_k` 不同时，不提供数值差异。CI 的阈值是内部回归保护，不是对实际大模型修复成功率的保证。

## 4. 限制与安全边界

- Python AST 是静态语法树级工具，而非完整 LSP、类型解析器或语义索引。特别是跨模块重导出、动态函数绑定、装饰器、副作用、反射以及 TypeScript/JavaScript 类型关系，都可能遗漏或误判。
- 名称相同不等于真正引用该符号。日志里的路径不等于错误归因，更不是执行指令。报告可以被有本地写权限的人篡改；生产使用需依靠可信执行环境、访问控制及持久证据链。
- 单文件检索默认上限 32 KiB、最多 3500 个受支持的源码文件，总计最多 16 MiB，AST 符号及引用数量另有硬上限。巨型代码库应先缩小项目范围。
- 源码不自动上传，不自动写入、提交或部署。更深入的 JS/TS 分析、真正大型独立开源项目评测、受控远程模型成功率实验仍属于未来范围。
