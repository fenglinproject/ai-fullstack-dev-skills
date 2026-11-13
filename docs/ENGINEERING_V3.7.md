# V3.7 — 增量索引、多语言符号与测试影响筛选

本版保留全部 144 个 Skill、审查审批和回退机制。新增三个**只读默认**工具，降低大型项目每次重新解析的代价，并为 Python/JavaScript/TypeScript 项目提供*候选*符号和受影响测试。注意：静态分析不会执行用户源码，但不能替代 LSP、完整运行时调用图或安全沙箱。

## 环境与验证

- Python 3.10+；纯 Python 项目无需 Node/TypeScript。
- 对 JS/TS 源码进行 AST 分析，需要 Node.js 20+ 和 TypeScript 编译器（验证环境使用 Node 22、TypeScript 5.9.3）。TypeScript 在工具环境中安装，例如 `npm install -g typescript@5.9.3`。仓库中的 TS 源码不会通过 `require`、tsconfig 插件或 eval 执行。
- 增量缓存是**显式写入**，默认仅读取可用缓存并返回分析结果；`--save-cache` 在项目 `.ai/cache/code_index_v37.json` 下保存路径、哈希、符号与依赖元数据。缓存不包含源码正文，但可能包含项目内部符号名称，应作为私有数据对待。

```bash
# 不写入缓存：查看简要统计
python tools/incremental_index.py --project benchmarks/projects/ts-workspace --summary

# 明确启用增量缓存；第二次运行应复用文件（parsed=0）
python tools/incremental_index.py --project benchmarks/projects/ts-workspace --save-cache --summary
python tools/incremental_index.py --project benchmarks/projects/ts-workspace --summary

# 跨语言符号查询，显示所在文件和行号
python tools/incremental_index.py --project benchmarks/projects/ts-workspace --query Checkout

# 候选测试集合（只建议，不自动执行）
python tools/test_selection.py --project benchmarks/projects/inventory-service --changed src/pricing.py
python tools/test_selection.py --project benchmarks/projects/ts-workspace --changed src/price.ts

# AI 代理本地上下文预览：不自动扩大可发送文件列表
python orchestrator/agent.py context --project benchmarks/projects/ts-workspace \
  --task-id DEMO37 --task "Adjust invoiceTotal calculation" \
  --include src/invoice.ts --multilang-hints

# 四个可见项目的固定评测（不是隐藏真实世界测试）
python tools/benchmark_v37.py --output benchmarks/v37_results.json
```

### 缓存与边界

- 每次对代码文件计算内容 SHA-256，文件内容变化即重新解析；即使修改时间未变化，也能识别更改。文件删除会从结果和新缓存移除。
- 跳过软链接、常见凭据文件、敏感内容、生成目录和超限文件；不会访问网络，不会执行用户源码。默认文件上限 5000、总读取量 48 MiB、单文件 256 KiB，超过资源上限时明确失败，而非截断后静默声称完整。
- JS/TS 通过独立 Node TypeScript 编译器进行 AST 语法解析；不运行项目 `package.json`、JS 导入或任何项目模块。TypeScript 编译器不可用时，新 JS/TS 分析会明确报错，不假装使用了 AST。
- 仅识别 Python 静态 import/from 和 JS/TS 常见相对静态导入；运行时反射、部分别名、tsconfig paths、monorepo workspace 映射和生成代码无法完全解析。
- `tools/test_selection.py` 根据导入关系反向遍历候选测试。未知文件、解析错误、动态导入、无法解析的本地导入或缺少匹配测试，会设 `full_suite_required=true`。即使 `false` 也**必须在合并前运行完整套件**；结果不证明覆盖完全。
- 对 `.ai` 缓存仍应按不可信本地数据处理。它仅用于优化解析；测试选择有静态盲区，不能作为生产发布的唯一依据。多进程可通过原子替换写缓存，但不提供并发事务锁。

## 兼容性和旧版修正

本版没有更改生产环境的默认检查配置。V3.6 原始包中的某些演示测试把 `init` 后默认禁用的检查当成已启用检查，导致本地完整回归失败。V3.7 仅在*受信任的测试 fixture* 和显式运行的离线演示中打开测试；新创建的普通项目依旧默认 `enabled=false`，需要用户确认测试来源后再启用。

## 独立示例验证

```bash
(cd benchmarks/projects/inventory-service && python -m unittest discover -s tests -v)
(cd benchmarks/projects/notes-workspace && python -m unittest discover -s tests -v)
node --test benchmarks/projects/js-dashboard/tests/report.test.js
tsc --project benchmarks/projects/ts-workspace/tsconfig.json --noEmit
# 可选：在临时目录编译 TS 后运行其无外部依赖的测试文件
TMP_DIR=$(mktemp -d)
tsc --project benchmarks/projects/ts-workspace/tsconfig.json --noEmit false --outDir "$TMP_DIR"
node "$TMP_DIR/tests/invoice.test.js"
rm -rf "$TMP_DIR"
```

四个项目均为仓库随附、可检查的教学样例，不应表述为对未见过的大型真实仓库的有效性验证；也没有外部 AI 模型调用结果。对于实际用户仓库，应另行明确授权、先排查敏感信息，并记录测试和性能基线。
