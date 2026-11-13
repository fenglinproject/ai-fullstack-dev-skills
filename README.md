# AI Fullstack Dev Skills · V5.0

> **中文说明**：这是一个含 **144 个专业 Skill** 的 AI 辅助软件开发工具包，提供技能路由、受审批的代码修改、测试与验收、Git 协作、本地 Web 看板及版本安装/升级/回滚。**不是无人工审核的自动编程平台，也不是安全沙箱。**
>
> **English**: A Python CLI and AI-assisted engineering toolkit with 144 skills, approval-gated code changes, validation workflows, Git collaboration, a read-only local dashboard, and managed releases. **Not an autonomous coding service or a security sandbox.**

## 文档导航 / Documentation

| 文档 | 内容 |
|---|---|
| [中文快速上手](docs/QUICKSTART_CN.md) | 环境要求、安装、基本命令、注意事项 |
| [详细安装、升级与回滚](docs/ENGINEERING_V5.0.md) | V5.0 生命周期管理完整教程 |
| [完整版本更新日志](CHANGELOG.md) | V2～V5 主要变化与历代详细日志 |
| [V5.0 Release Notes](RELEASE_NOTES_V5.0.md) | 可以复制到 GitHub Release 的发布说明 |
| [GitHub 发布指南](docs/GITHUB_PUBLISH_CN.md) | 建仓、推送、Release、校验及公开前检查 |
| [技能索引](SKILLS_INDEX.md) | 144 个 Skill 的功能入口 |
| [Agent 接入说明](docs/AGENT_INTEGRATION.md) | 模型调用、变更提案与权限边界 |
| [安全说明](SECURITY.md) | 运行风险、权限和模型数据外传限制 |
| [测试证据](RELEASE_VALIDATION_V5.0.md) | 本地测试结果与未验证范围 |

## 功能概览 / Features

- **Skill Routing**：面向需求、前端、后端、数据库、测试、发布等任务的路由与风险分级。
- **Approval-gated workflow**：预览差异 → 人工确认 → 修改 → 测试 → 验收 → 必要时回滚。
- **Repair sessions**：最多 5 轮的可暂停修复流程，每一轮仍要求授权。
- **Code intelligence**：Python、JavaScript/TypeScript 符号索引、有限静态依赖与测试影响提示，可选可信 LSP。
- **Git & CI**：只读仓库检查、本地受控提交、跨 worktree 协作锁和 CI 证据核对。
- **Read-only dashboard**：本机 `127.0.0.1` 可视化项目状态、验收、修复记录和 Git 元数据。
- **Release lifecycle**：V5.0 增加侧并安装、完整性验证、版本切换与可回滚管理。

## 快速运行 / Quick Start

**要求**：Python 3.10+（推荐 3.11）；可选 Git、Node.js 22、TypeScript 5.9.3、clangd 等，只在相应功能中需要。基本 CLI 无需额外 `pip install`。

```bash
# 在本仓库根目录执行
python fullstack.py --version
python fullstack.py --help
python fullstack.py doctor

# 根据任务路由技能
python fullstack.py route --task "开发一个用户管理系统"

# 只读供应链规则审计
python fullstack.py supply-chain audit

# 查看发布验收计划（默认不执行）
python fullstack.py release-matrix --shard all

# 启动仅限本机访问的只读项目看板
python fullstack.py dashboard --project project --port 0 --open
```

Windows 可在 PowerShell 使用 `py -3 fullstack.py --help`（需安装 Python Launcher），或在系统 Python 已入 PATH 时使用 `python`。启动看板后请勿公开其令牌或把本地端口映射到公网。

### 运行测试（仅可信源码）

```bash
python fullstack.py release-matrix --shard all --execute
```

`--execute` 会运行随包测试代码。**不要在含不可信脚本、密钥或生产权限的环境中执行未经审查的仓库代码。**

### 管理版本（V5.0）

```bash
python fullstack.py lifecycle --help
```

安装前应取得独立可信来源的 ZIP SHA-256，然后使用 `lifecycle plan` 预览、`install --approve` 安装、`upgrade --approve` 切换；完整可复制命令见 [生命周期管理教程](docs/ENGINEERING_V5.0.md)。

## 目录结构 / Layout

```text
.
├── fullstack.py                 # 统一 CLI
├── skills/                      # 144 个专业 Skill
├── orchestrator/                # Agent、审批、代码修改和状态管理
├── tools/                       # 检索、测试、评测、发布与安装工具
├── dashboard/                   # 本地只读 Web 看板
├── examples/                    # 演示项目
├── benchmarks/                  # 固定离线评测数据
├── tests/                       # 回归测试
├── docs/                        # 使用教程与工程文档
├── .github/workflows/           # CI 工作流定义
├── CHANGELOG.md                 # 版本概览
└── RELEASE_VALIDATION_V5.0.md  # 本地测试说明
```

## 验证状况 / Verification

V5.0 发布记录显示：本地 Linux 环境分组执行 **431 项 Python 测试**，路由基准 **28/28**，Smoke **4/4**。具体条件见 [发布验证报告](RELEASE_VALIDATION_V5.0.md)。

**尚未验证**：真实 GitHub Actions 的 Linux/Windows/macOS 运行回执、可信发布者签名、npm Registry 联网安装与真实生产仓库。仓库内有 CI 配置不代表线上测试已经成功。

## 安全与许可证 / Security & License

- 所有外部模型源文件上传必须由用户显式批准；规则和扫描不是完整 DLP。
- 测试和 LSP 可以执行代码，不构成操作系统级隔离沙箱。
- 原始 [`LICENSE`](LICENSE) 声明为 MIT，但发布者必须先核实版权归属、补全正确版权信息和标准许可文本，并审查引用的第三方素材授权。
- 不应上传私钥、令牌、业务数据、`.env`、`.ai/` 私有运行状态或测试输出中的敏感信息。

Contributions and issue reports are welcome subject to the repository maintainer's policies. Please avoid posting secrets in public issues.
