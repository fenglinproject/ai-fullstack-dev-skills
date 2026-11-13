# V3.8 — Monorepo 工程分析、增量依赖图、离线 LSP 信息导入与性能评测

V3.8 保留 V3.7 所有 144 个 Skill、代码提案审批、测试授权、恢复机制、项目状态和 Git 审查流程。此版只增加**默认只读**的工程分析与离线评测工具；**不会执行仓库安装脚本、项目代码、LSP 服务端或任何模型接口**。

## 前置条件

- Python 3.10+（与 V3.7 相同）。
- JS/TS AST 解析需要 Node.js 与工具环境中的 TypeScript 编译器。不会读取/执行项目里的 TypeScript 插件或 package 脚本。
- 没有 JS/TS 的 Python 项目不需要 Node。

## 1. 静态 Monorepo 工作区识别

```bash
python tools/monorepo_workspace.py --project /path/to/repo
```

- 静态读取**根目录** `package.json` 中 npm/yarn 的 `workspaces`，以及 `pnpm-workspace.yaml` 中静态 `packages:` 列表；识别本地包名、相对目录、入口候选。
- 能将包名导入 `@scope/pkg` 和 `@scope/pkg/path` 的若干常见引用连接为代码索引中的静态依赖边，辅助 `tools/test_selection.py` 找到跨工作区的候选测试。
- pnpm YAML 只接受**静态列表**，不执行 YAML tags、插件、脚本或工作区钩子；不支持 `**` 递归 globs（防止不受控遍历），建议显式列出 `packages/*`、`apps/*` 等模式。
- 未覆盖全部 Node 模块解析机制：不解析复杂 `exports` 条件、tsconfig `paths`、运行时代码生成和动态模块加载。对于不确定引用，会设置保守提示，不得将结果用作跳过完整测试的依据。

## 2. 增量依赖图（可审计、可选保存）

```bash
# 仅读取，不写入项目
python tools/incremental_graph.py --project /path/to/repo

# 明确允许保存快照到 .ai/cache（下一次比较基线）
python tools/incremental_graph.py --project /path/to/repo --save

# 修改代码后，仅预览变化和上下游影响，不写入新快照
python tools/incremental_graph.py --project /path/to/repo --changed packages/core/src/index.ts

# 验证无误后保存新快照作为下次基线
python tools/incremental_graph.py --project /path/to/repo --save
```

新工具输出 `files_added`、`files_deleted`、`edges_added`、`edges_removed`、`affected_dependents` 和 `caution_flags`。依赖图和原代码符号索引缓存存于 `.ai/cache/`，以原子替换写入；软链接缓存路径被拒绝。缓存不包含源码正文，但**文件路径和符号名可能属于私有信息**，不得随意分享；缓存内容不得被视为可信指令。

现有的 `tools/test_selection.py` 已通过升级的索引自动获得跨工作区静态依赖；仍有深度上限，超过上限、发现动态或未解析导入时会标记 `full_suite_required=true`。即使标记为 `false`，发布前仍需要完整测试。

## 3. LSP 符号位置：**离线导入**，不运行语言服务器

本版不包含完整的 LSP 客户端，也不启动语言服务器。用户可以从*自己已有*的语言服务器导出 WorkspaceSymbol/Location 类型 JSON，再手工导入：

```bash
python tools/lsp_import.py --project /path/to/repo \
  --export /path/to/lsp_export.json --query calculate --limit 20
```

支持如下格式：

```json
{
  "symbols": [
    {
      "name": "calculate",
      "location": {
        "uri": "file:///absolute/path/to/repo/src/math.py",
        "range": {"start": {"line": 5, "character": 0}}
      }
    }
  ]
}
```

位置是 LSP 的 **0-based line**，输出转换为 **1-based**。拒绝项目外 URI、HTTP URI、软链接、未纳入 AST 索引的敏感/超限文件和损坏记录。外部导出的符号位置未经验证，因此仅为候选，不视作真实调用关系或授权向模型传输源码。

## 4. 小型生成式 Monorepo 性能评测

```bash
python tools/benchmark_v38.py --modules 48 --output benchmarks/v38_results.json
```

工具在**临时目录**生成一个由 48 个互相引用的 TypeScript 包构成的可见样例，测量冷启动、复用缓存、单文件修改后的解析文件数和耗时，并验证依赖与测试候选是否能被找到；退出后自动删除临时项目。计时依赖机器与系统负载，**不是**真实大型开源仓库的独立验证，也不代表实际模型修复成功率。`candidate_full_suite_required` 应原样报告，不能因候选测试命中就声称可以跳过全量检查。

## 5. 真实模型修复前后对比：仅汇总**用户提供**的成对结果

如果已经通过外部编程代理或 CI 得到了同一组任务的前后独立验收结果，可通过 JSON 输入比较：

```json
{
  "schema_version": 1,
  "cases": [
    {"id": "case-A", "before_pass": false, "after_pass": true},
    {"id": "case-B", "before_pass": true, "after_pass": true}
  ]
}
```

```bash
python tools/benchmark_v38.py --paired-results /path/to/outcomes.json
```

输出前后成功率、改善/退步数量和绝对差异。此工具**不会实际调用大模型、创建数据集或核查输入的真实性**。开展可信的模型对比时应固定模型版本、提示词与权限、任务集、随机种子（适用时）、成本和独立测试环境，并保留原始结果供复查。

## 安全与目前的边界

- 默认只读，不联网，不执行用户源码；保存依赖快照须显式 `--save`。
- Monorepo 解析为有限模式，支持常见 npm/yarn/pnpm 静态配置，但不是全面的包管理器/LSP 解析器。
- LSP 功能**仅导入**已有 JSON；没有实现标准 JSON-RPC LSP 会话和自动服务器启动。
- 性能基准来自生成式小型样例，不代表未知真实大型仓库；模型成功率只有提供真实配对结果时才能计算。
- 所有自动生成的候选位置/测试清单都只能辅助审查，不能绕过 V3.0+ 的文件修改审批、模型源码共享授权或全量 CI 验收。
