# V3.3 工程协作：隔离测试、Git、代码审查与依赖影响

V3.3 保留 V3.2 的 144 个 Skill、人工审批和多轮修复流程，新增以下**显式调用**的本地工具。需要 Python 3.10+；Git 工具需要安装 Git。Docker 容器测试需要单独安装并安全配置 Docker，且**只使用可信、摘要固定的镜像**。

## 1. 独立测试快照（Docker，可选）

在现有项目初始化后，先编辑 `.ai/checks.json` 并启用相应的检查。先预览：

```bash
python tools/isolated_checks.py --project /path/to/project --image 'python@sha256:<真实且已验证的64位sha256镜像摘要>'
```

将上述占位符替换为**可用且可信的真实镜像摘要**。确认检查范围后才添加 `--run`：

```bash
python tools/isolated_checks.py --project /path/to/project --image 'python@sha256:<真实摘要>' --run
```

工具先复制一个有限的临时源码快照，跳过 `.git`、`.ai`、常见密钥文件、依赖缓存，拒绝符号链接和超限文件，然后使用 Docker `--network none`、只读源码挂载、只读根文件系统、非 root 用户、禁止特权提升、限制 CPU/内存/进程数量，在容器中执行已有白名单测试。快照本身不会执行任何源码。容器退出后删除临时副本。

**重要限制**：Docker **不是不可逃逸的安全边界**；宿主机 Docker 守护程序、镜像、内核和挂载策略必须可信。不会安装依赖；缺失测试依赖会导致测试失败。跳过的项目文件也可能改变测试行为；此流程只适合无需外部网络/凭据的测试。容器测试不能替代安全审计。当前发布环境**没有 Docker**，只验证了选项约束、快照、Docker 命令结构及模拟执行，**没有验证真实 Docker 容器内的运行结果**。

V3.0 工作流与 V3.2 多轮循环可选择容器测试（均保留显式授权）：

```bash
python orchestrator/workflow.py verify --project /path/to/project --change-id CHANGE_ID \
  --isolated-image 'python@sha256:<真实摘要>' --run --close-task
python orchestrator/loop.py test --project /path/to/project --run-id RUN_ID \
  --isolated-image 'python@sha256:<真实摘要>'
```

不指定 `--isolated-image` 时，原有 `--run` 和 `--trust-project-code` 仍然使用**受信任本机项目**的测试运行器，绝不应误认为隔离运行。

## 2. 静态依赖分析与代码审查

```bash
python tools/dependency_graph.py --project /path/to/project --changed src/service.py src/types.ts
python orchestrator/code_review.py --project /path/to/project --change-id CHANGE_ID
```

依赖扫描读取 Python AST 的本地 import，以及 JS/TS/Vue 部分相对导入语法，并输出潜在的直接依赖和反向受影响文件。它**不会执行代码**。动态加载、tsconfig aliases、包级别导入、数据库字段、运行时数据流暂不支持语义级分析。静态审查检查新增代码中的可能密钥、危险动态调用、临时调试内容与空白字符；规则结果只能提示人工复核，不能作为“安全通过”的证明。

## 3. 本地 Git 分支、受控提交、离线 PR 草稿

**在修改源码之前**，使用一个已初始化、干净的 Git 仓库执行：

```bash
python orchestrator/git_collab.py branch --project /path/to/project --name ai/task-123 --approve
```

随后按 V3.0/V3.2 流程预览提案、审批修改并运行测试，取得 `CHANGE_ID`：

```bash
python orchestrator/git_collab.py commit --project /path/to/project --change-id CHANGE_ID \
  --message 'Fix task implementation' --approve
python orchestrator/git_collab.py draft-pr --project /path/to/project --change-id CHANGE_ID \
  --title 'Fix task implementation' --base main
```

提交前检查：当前在 `ai/*` 分支；文件哈希与变更记录一致；存在**对应 change_id 的已执行且全部通过的测试报告**；Git 暂存区为空、工作树仅包含本次批准的源文件。只把批准的文件纳入提交，并关闭本地 Git hooks。**仍只用于可信 Git 仓库**，因为恶意 Git config/filters 在 `git add` 期间可能执行命令。脚本不会自动 `push`、打开线上 Pull Request、合并或部署。PR Markdown 草稿保存在 `.ai/pr-drafts/`，需要人工进一步审查并上传到代码托管平台。

更复杂的项目建议先建立受保护的分支规则和 CI，并由维护者复核 PR 与测试证据。人工确认/自动化测试证据不是安全认证，也不能代表生产发布授权。

## 4. 命令清单与能力边界

| 新命令 | 会修改什么 | 风险边界 |
|---|---|---|
| `tools/dependency_graph.py` | 不修改源码 | 静态推断可能不完整 |
| `orchestrator/code_review.py` | 不修改源码 | 只是启发式扫描 |
| `tools/isolated_checks.py` | 临时副本；`--run` 执行 Docker | 必须信任 Docker 守护程序和镜像 |
| `git_collab.py branch` | 显式批准后创建本地分支 | 需要干净 Git 工作树 |
| `git_collab.py commit` | 显式批准后 Git add/commit | 可信仓库，且测试证据存在 |
| `git_collab.py draft-pr` | 创建本地 Markdown 草稿 | 绝不上传远端 |

本版本没有在线 PR 创建、跨仓库重构、生产部署或真实 Docker 端到端证明。
