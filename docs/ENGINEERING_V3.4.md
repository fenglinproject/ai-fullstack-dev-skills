# V3.4 工程能力：静态语义提示、GitHub PR/CI、修复质量统计

V3.4 继承 V3.3：144 个 Skill、显式审批的源文件变更、最多五轮修复、有限本地检查、可选 Docker 运行器、本地 Git 分支与提交。新增模块只读取必要数据；任何远程写入仍需要额外授权。

## 1. Git 基线符号影响分析（只读）

在 Git 项目根目录、**修改源码后但提交之前**执行：

```bash
python tools/semantic_impact.py --project /path/to/project --changed src/service.py
```

它会读取 `HEAD` 的对应文件和当前工作树，对比 Python 顶层函数的参数/返回注解、类基类与方法名，列出增删/签名变化的符号；随后提示直接 `from ... import ...` 引用该符号的代码文件，以及已有依赖图中的反向影响文件。此操作不会执行项目代码或联网。未找到 Git 基线时，报告明确标记为 unavailable，不猜测变化。

这 **不是完整语义分析器**：不跟踪函数体逻辑变化、运行时数据流、数据库字段、反射调用、依赖注入、重导出、TS/JS 类型系统或全部复杂相对导入。Git 提交后 `HEAD` 可能已变为新版本，此时相同签名不代表改动没有影响。报告只能帮助确定人工审查范围。

## 2. GitHub CI 与在线 Draft PR（需要 GitHub CLI）

前提：将项目初始化为可信 Git 仓库，并配置真实的 GitHub `origin`；用户自行配置并登录 `gh` (`gh auth login`)，根据仓库策略配置分支保护和 CI。工具只支持 `github.com` HTTPS/SSH origin，不接受其他域名或自定义主机。不要将 API token 写入命令或日志。可参考：

- https://cli.github.com/manual/gh_pr_view
- https://cli.github.com/manual/gh_pr_create

### 查询已有 PR 的检查

```bash
# 默认仅预览将调用的命令，不触网
python orchestrator/github_ci.py checks --project /path/to/project --pr 12

# 明确执行只读远程查询
python orchestrator/github_ci.py checks --project /path/to/project --pr 12 --execute
```

`all_checks_successful` 仅归纳 API 返回的非空检查列表，空列表不会视为通过；它**不是**分支保护、审查批准或可合并状态的最终结论。

### 创建 Draft PR

须先完成 V3.3 本地流程：`branch`、经审批的 `apply`、实际执行的 `verify`、`commit`、`draft-pr`。**开发者需要自己把分支推送到适当远程仓库**；本工具不会执行 `git push`。

```bash
# 先预览；不会调用 gh、不会自动创建 PR
python orchestrator/github_ci.py publish --project /path/to/project --change-id CHANGE_ID \
  --title 'Fix selected implementation' --base main

# 独立授权后才实际创建 Draft PR；不会合并/发布
python orchestrator/github_ci.py publish --project /path/to/project --change-id CHANGE_ID \
  --title 'Fix selected implementation' --base main --execute --approve
```

执行前核对 `ai/*` 分支、干净工作区、本地提交文件与变更清单完全一致、同一 `change_id` 对应已执行且通过的本地测试证据，以及本地 PR 草稿。命令使用 `gh pr create --head ai/... --draft`；根据 GitHub CLI 官方说明，显式指定 `--head` 可以跳过隐式 fork/push。创建失败或超时时需先查询远程是否已经建立 PR，**不可盲目重试**。

真实远程账号、权限与网络访问需要使用者自己提供。本包仅以模拟 GitHub CLI 输出验证了接入逻辑，并未使用真实密钥访问线上仓库。

## 3. 修复会话质量指标（只读，本地）

```bash
python tools/loop_metrics.py --project /path/to/project
```

从 `.ai/loops/loop-*/state.json` 计算会话数量、完成率、轮次、失败轮次、通过轮次和端到端平均耗时。默认最多读取 500 个会话，可用 `--max-runs` 在 1～2000 之间调整。汇总**不输出任务内容或源码**；遇到损坏/不符合格式的记录会跳过并给出警告。

指标反映本地保存的会话状态，不独立证明代码质量；耗时包含人工审核等待，并非模型计算耗时或实际工时。需要跨版本比较时应固定任务集、运行环境、测试配置和抽样口径，避免用单一完成率判断系统能力。

## 4. CI 模板

`.github/workflows/test.yml` 在 push/PR/手动触发时执行源码编译、目录审计、全部单元测试、路由基准和示例 API 测试；并上传审计结果与路由基准文件供维护者审查，保持 `contents: read` 最小权限。`.github/pull_request_template.md` 提供人工审查清单。需要在实际 GitHub 仓库启用 Actions 和保护分支，才能形成真实线上 CI 结果。

## 5. 权限边界

| 操作 | 默认行为 | 显式操作 |
|---|---|---|
| 符号影响扫描、修复指标 | 仅本地读取 | 无 |
| GitHub CI 检查 | 预览，不联网 | `checks --execute` |
| GitHub Draft PR | 预览，不联网 | `publish --execute --approve` |
| Git push、PR 合并、部署 | 不支持 | 需到外部平台人工操作 |

**可信项目要求**：仓库可能包含恶意 Git 过滤器、配置或第三方工具；仅在可信的本地开发环境中操作。GitHub Actions 必须由仓库维护者审查后再启用，尤其不要对不可信 PR 授予写权限。
