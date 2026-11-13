# V4.3 工程指南：独立 Git 仓库验证、证据完整性与长期记录审计

## 1. 升级目标

本版本在 V4.2 的任务增长、证据与只读仪表盘基础上，验证连续本地 Git 开发过程，并修复两类跨版本问题：

1. **提交后误报源码漂移**：原工作流的 `applied` 不区分尚未提交与已提交的历史变更。当同一文件被后续任务修改时，早期变更记录会误报。V4.3 在受控 `git_collab.commit` 成功后记录 `committed`、`git_commit`、`committed_at`。历史变更按**对应 Git 提交中的文件内容**校验，而不是永远对比当前工作区。
2. **提交证据过于宽松**：原提交代码根据 change_id 查找“任意一份通过报告”。V4.3 将最近一次验证报告的 SHA-256、验证时 Git HEAD 和修改文件内容哈希保存到变更清单。提交前核对这些证据；重新测试失败将替换最新验证状态，旧的成功报告不能自动用于提交。

这套校验能够识别意外变更、缺失证据和部分本地篡改，**不是不可伪造的签名**：同一用户若能够任意改写 `.ai` 文件，仍可能伪造本地记录，正式 CI 应使用独立受控环境。

## 2. 只读检查实际 Git 仓库

必须在已有 Git HEAD 的**仓库根目录**运行：

```bash
# 默认只读取 Git 元数据和 .ai 内的项目记录，不执行用户代码
python fullstack.py audit-repo --project /absolute/path/to/repo

# 固定基线，要求工作区无未提交内容
python fullstack.py audit-repo \
  --project /absolute/path/to/repo \
  --expected-head FULL_40_CHAR_GIT_SHA \
  --require-clean

# 可独立使用，检查失败返回非零退出码
python tools/repo_health_v43.py --project /absolute/path/to/repo
```

输出包含：`git`（HEAD、分支、脏文件数量）、`counts`（任务、报告、状态）、`errors`、`warnings` 和 `healthy`。工具不返回源码、测试标准输出、提案正文或备份。对 `prepared` 的中断记录只警告，**不会擅自回退、重置或修复项目**。

扫描默认限制每类最多 1000 条记录；超过上限会显式报告错误。仅处理 `.ai` 中约定的结构，不应把这个轻量审计当作全面安全或合规审计。某些 Git 配置/扩展仍可能在只读命令中调用本机程序，因此只对可信 Git 仓库使用。

## 3. 连续开发与验收演示

```bash
# 默认：只预览，不执行项目测试
python examples/v43-repo-demo/run_demo.py

# 在临时复制的可信示例仓库中执行三轮：审批、测试、提交、验收
python examples/v43-repo-demo/run_demo.py --execute-tests --rounds 3

# 五轮连续提交与报告，独立本地 Git 工作区
python examples/v43-repo-demo/run_demo.py --execute-tests --rounds 5
```

每次运行都会在系统临时目录复制 `examples/workflow-demo`，自行建立 Git 仓库与专属 `ai/*` 分支，并生成真实本地 Git 提交。随后执行**随包可信 Python unittest 代码**、生成证据、验证任务状态、生成本地 PR 草稿、读取仪表盘快照及仓库审计结果，最后删除临时副本。它不会向任何 Git 远程推送，不调用大模型、GitHub API、部署或生产服务。

## 4. 新的变更清单状态

- `prepared`：备份已保存，但写入尚未确认完成；可能由进程中断产生，需人工检查。
- `applied`：文件已修改但未通过受控 Git 提交流程提交；仍检查当前源码哈希，可在无漂移时经明确授权恢复。
- `committed`：受控本地提交已完成，记录 Git SHA；审计时比较对应提交里的文件内容，**不会通过 restore 自动重写已提交的历史**。撤销提交应走单独审查的 Git 工作流。
- `restored` / `aborted`：对应原有回退或失败状态。

旧版本中已提交但仍保留 `applied` 的清单，**不会被自动迁移为 `committed`**，以免推断错误 Git 提交。应由用户审查历史记录再处理；旧版未附有 `last_verification` 的记录可能需要重新运行测试才能通过 V4.3 的新提交门禁。

## 5. 回归测试与使用边界

```bash
python -m unittest tests.test_v43 -v
python -m unittest tests.test_v33 tests.test_v34 -q
python tools/audit_catalog.py
python tools/benchmark_router.py
python fullstack.py verify --profile smoke --execute
```

本版没有在公开未知大型仓库、生产级持续开发或真实线上 GitHub PR 上做独立评估。默认测试运行器**不是安全沙箱**；不得直接执行未经审查的外部仓库测试。全量历史测试推荐按模块分组执行；整包单进程发现式运行曾出现超时，不能把超时视为通过。
