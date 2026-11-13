# V3.7 — 大型项目工程化增强版

- 新增 `tools/incremental_index.py`：Python/JS/TS 统一增量符号索引，SHA-256 内容变更检测、删除失效、显式私有缓存；严格限制大小/文件数量并跳过软链接和凭据文件。
- 新增 `tools/ts_ast_bridge.cjs`：使用 TypeScript compiler AST 读取 JS/JSX/TS/TSX 的类、函数、方法、导入与静态调用线索；不执行被分析项目的模块。
- 新增 `tools/test_selection.py`：基于静态导入关系反向遍历候选受影响测试；异常路径和不可解析依赖要求全量验证。
- `orchestrator/agent.py` 增加 `--multilang-hints` **只读**预览，不改变模型源码白名单。
- 增加 JS CommonJS/TypeScript 双独立测试 fixture、四项目基准 `tools/benchmark_v37.py` 和新增回归 `tests/test_v37.py`。
- 修复继承自 V3.6 的历史演示测试授权假设：只在测试 fixture 和用户手动运行的受信任 demo 中显式开启检查，普通项目默认关闭。
- 更新 CI 和发布记录。**不包含自动网络调用、自动推送、自动部署、沙箱化任意源码或完整 LSP 解析。**
