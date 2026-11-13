# V3.9 · LSP 协议、工程配置解析与独立仓库评测

本版保留 V3.8 的全部原有技能、审批、变更回退和静态评测能力。

## 1. LSP 客户端：显式授权的本地可执行进程

新增 `tools/lsp_client.py`，实现基于 `Content-Length` 的 LSP/JSON-RPC 2.0 stdio 通信：

- `initialize` → `initialized` → `workspace/symbol` / `textDocument/definition` → `shutdown` → `exit`；
- 设置帧大小、通知数、等待时间、输出结果、子进程参数上限；超时终止服务器；
- 对于服务器主动请求，回复“不支持”，不允许服务器触发客户端文件写入或其他动作；
- 仅返回索引内源文件的位置候选，拒绝外部 URI、软链接和未收录文件；
- 需要**主动指定可执行程序的绝对路径**和 `--allow-start`，不会自动下载或启动服务器。

```bash
python tools/lsp_client.py \
  --project /absolute/path/to/project \
  --server /absolute/path/to/trusted-language-server \
  --allow-start \
  --query MySymbol

python tools/lsp_client.py \
  --project /absolute/path/to/project \
  --server /absolute/path/to/trusted-language-server \
  --allow-start --definition src/example.ts --line 9 --character 4
```

**必须理解**：LSP 服务器本身是可执行的第三方程序，它可能执行项目配置、读取敏感文件、访问网络；这里没有提供进程级沙箱或强制网络隔离。环境变量会限制到常用运行变量，但这不构成沙箱。请只在可信项目与可信程序上运行。位置结果仍是*候选结果*，不代表语义完全正确。当前仅实现两类请求，不支持完整编辑器级 LSP 功能或多服务端编排。

本地协议验证使用 `tests/mock_lsp_server.py` 独立子进程测试真实 stdio 帧；**不是对外部真实语言服务器的验证**。如未安装可信语言服务器，可以继续使用 V3.8 的离线 `tools/lsp_import.py`。

## 2. TypeScript / JavaScript 项目配置

新增 `tools/project_config.py`，**只读**分析：

- `tsconfig.json` / `jsconfig.json` JSONC（行注释、块注释及尾逗号）；
- 位于仓库内的相对 `extends`、`references`、静态 `compilerOptions.baseUrl` 和 `paths`；
- 工作区 `package.json` 静态 `exports`（部分 `import` / `require` / `types` / `default` 条件）；
- 增量 AST 索引会消费路径别名与包导出，为静态反向依赖和候选测试选择提供额外边。

```bash
python tools/project_config.py --project /absolute/path/to/project
python tools/incremental_index.py --project /absolute/path/to/project --query MySymbol
python tools/test_selection.py --project /absolute/path/to/project --changed packages/utils/src/index.ts
```

**限制**：不执行 JS/TS 配置、包管理器、插件；不支持通配符子路径 `exports` 的完整运行时决议、package-based `extends`、所有 condition exports、所有打包器自定义路径、网络依赖或 pnpm 的所有 workspace glob。解析不全会标记 warning；测试选择收到不完整工程配置告警时要求完整测试。静态依赖不是完整运行时调用图。

## 3. 独立 Git 仓库只读评测

新增 `tools/external_repo_benchmark.py`。用户自备 **独立的、已初始化且工作区干净的本地 Git 仓库**，提供绑定到当前 40 位 Git SHA 的人工标注案例。评测期间不会执行该项目的脚本、运行单元测试、克隆远程仓库、调用外部模型或写入被测仓库；工具会在结束时再次检查 Git 工作区。

```bash
# 先用 git rev-parse HEAD 获取仓库当前提交，将其写到标注文件 commit_sha
python tools/external_repo_benchmark.py \
  --project /absolute/path/to/independent-repo \
  --manifest /absolute/path/to/cases.json \
  --repeats 2 \
  --output /absolute/path/outside-repo/v39_report.json
```

案例结构见 `benchmarks/v39_external_manifest.example.json`，包括 `symbol_cases` 和 `test_cases`。每个预期文件必须是 Git 跟踪文件；评测报告包含 SHA、标注文件哈希、符号命中/排名、受影响测试命中、执行耗时中位数，以及配置警告。不报告外部 AI 修复成功率，也不声称人工标签经过独立验证。

这里的“独立仓库评测”指**提供工具和验证协议**。本次交付仅以单独创建的临时 Git 仓库完成端到端测试；由于构建环境无法解析 github.com，未能从公共代码托管平台获取并评测真实开源仓库。这是待完成的外部验证，而非已完成的 V3.9 成果。

## 4. 安全与验收

- 不向外部模型自动发送检索出的源码；代码修改仍需走 V3.x 原有提案与人工审批；
- 不默认运行 LSP 服务器；LSP 子进程并非 sandbox；
- 不执行仓库脚本或 Git hooks；独立仓库须干净、指定明确 SHA；
- 可能漏报的动态加载与不完整配置需完整回归测试；
- 单元测试、固定样例测试和真实未知仓库基准的有效性分别评估，不混为一谈。
