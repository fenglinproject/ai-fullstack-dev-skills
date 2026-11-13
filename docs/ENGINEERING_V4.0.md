# AI Fullstack Dev Skills V4.0 — 统一开发控制台与工程验收

## 1. 版本定位

V4.0 把 V2–V3.9 分散的常用开发辅助工具收拢为**一个命令行入口** `python fullstack.py`，不是网页 GUI、云端 Agent 或无需审批的自动编程平台。全部 144 个原始 Skill、审批式提案、人工授权测试、回退、Git、Monorepo、静态分析和已有工具均保留。

运行环境：Python 3.10+；JS/TS AST 需要 Node.js + TypeScript；C/C++ LSP 示例需要用户自己安装并信任 clangd。**默认无网络连接、无外部模型调用、不修改源码，也不执行项目测试。**

## 2. 快速使用

在压缩包根目录执行：

```bash
python fullstack.py --help
python fullstack.py doctor
python fullstack.py route --task "优化按钮 CSS，不修改登录逻辑"
python fullstack.py project init --project project
python fullstack.py project status --project project
python fullstack.py index --project benchmarks/projects/ts-workspace --query Checkout
python fullstack.py select-tests --project benchmarks/projects/ts-workspace --changed src/price.ts
python fullstack.py check --project project                # 预览；不运行
python fullstack.py verify --profile smoke                # 仅预览固定验证清单
```

### 需要明确授权的操作

```bash
# 运行已经审查的本地项目测试；不是沙箱
python fullstack.py check --project project --execute --save-report

# 使用可信本地 LSP 服务器；绝对路径由使用者确认
python fullstack.py lsp --project /my/cpp/project \
  --server /absolute/path/to/clangd --server-arg=--background-index=false \
  --definition main.cpp --line 1 --character 19 --allow-start

# 执行本工具包固定的自测/示例测试（只运行随包样例）
python fullstack.py verify --profile smoke --execute
python fullstack.py verify --profile full --execute
```

多轮 AI 提案生成、人工批准、恢复、Git 分支和 PR 草稿仍可通过 `orchestrator/agent.py`、`orchestrator/loop.py`、`orchestrator/workflow.py` 以及 `orchestrator/git_collab.py` 使用。统一 CLI 暂未覆盖每个低频操作：旧入口不作废。

## 3. 真实语言服务器验证

V3.9 的 LSP 客户端此前只有模拟服务器协议测试。V4.0 在当前构建环境中使用 **clangd 17** 真实子进程，对临时 C++ 文件发送 `initialize`、`initialized`、`textDocument/didOpen` 和 `textDocument/definition`，返回 `main.cpp` 第 1 行的函数定义。新代码增加 C/C++ 源码候选发现，限定文件/总字节数、拒绝链接文件和明显敏感文本。**clangd 进程本身有执行与项目文件访问能力，且不是沙箱。**

此验证**不代表** TypeScript/Python 真实第三方语言服务器、未知大仓库、远程 GitHub 或外部大模型已被实际测试。LSP 查询结果仅是候选定位，不直接允许代码修改或源码外传。

## 4. 统一工程验收

`verify` 只提供固定的随包验证命令；它不读取用户提供的脚本或任意 shell 命令。默认仅显示计划，`--execute` 才会运行受信任的工具包与示例测试。所有步骤记录 `passed`、`failed`、`skipped`、`planned`，并打印进度到 stderr；测试总数、步骤数和是否执行需分开理解。

- `smoke`：目录审计、28 条路由基准、V4.0 单元测试、Todo API 测试。
- `full`：以上检查 + **逐模块进程隔离**的历史单元测试、Node/TS 样例、离线双轮修复、V3.5–V3.8 固定基准。单次完整执行耗时可能较长；应读取结果而非将超时视为通过。
- `--output benchmarks/reports/<name>.json`：仅在已明确 `--execute` 时创建本地 JSON 报告，不允许写入其他源码路径。

对用户独立 Git 仓库的测试：

```bash
python fullstack.py benchmark --project /trusted/clean/repo \
  --manifest /trusted/manifest.json --repeats 2
```

这仅做固定 SHA 的本地静态索引与测试候选分析，**不自动克隆、不运行仓库代码、不调用远程 API**。需使用用户提供、经过人工核对的标签清单；其正确性无法由系统担保。

## 5. 安全与保留能力

- `project` 状态写入、`index --save-cache` 和 `check --execute --save-report` 是**显式有副作用操作**。
- `--allow-start` 只授权指定本地语言服务器启动，不授权 Git push、线上 PR、数据外发或部署。
- `check` 即使限制了命令语法，也**不能安全隔离恶意测试代码**；不要在带密钥的宿主机执行不可信项目。
- 所有源代码修改继续沿用 V3 的提案差异、哈希校验、风险复核与审批流程；统一入口没有绕过任何审批。
- `doctor` 只检查环境及工具是否存在，不安装软件，也不保证 Docker daemon、网络、安全配置可用。
- 自测的多轮修复是离线演示，不代表真实模型修复率。

## 6. 下一步实际工作

1. 用明确授权的真实 Python/TS 语言服务器重复运行工作区符号、跳转和大型仓库索引。
2. 在外部仓库上制作人工校验过的固定提交评测清单，记录性能、准确率、失败原因及版本回归。
3. 在隔离的开发/CI 环境中使用真实 API 与模型，进行有人工审批、可追踪成本的代码修复 A/B 测试。
4. 如确有需要，再提供基于统一 CLI 的可视化仪表盘，而不是重复开发底层规则。
