# V4.6 工程指南：强制协作写入锁与中断事务核对

V4.6 在 V4.5 的人工 worktree 预留锁之上增加了**对本工具包参与的写入入口生效**的 Git 公共目录操作锁，并支持两种中断恢复诊断：`prepared` 源码写入中断与 `commit` 本地 Git 提交记录中断。仍保留 144 个 Skill，审批、测试证据、Git 操作均不自动执行。

## 1. 安全边界

- 对 Git 仓库，`workflow.apply / restore / verify`、`git_collab.branch / commit` 和 V4.6 的恢复入口在 Git common-dir 使用同一个操作锁。不同的 linked worktree 共享它。普通非 Git 项目保留原来的 `.ai/task_state.lock` 机制。
- 旧版 `worktree-lock acquire` 的人工预留锁现在会阻止这些参与入口写入，只有提供匹配的 `--worktree-token` 才能继续。
- **不能拦截 Git CLI、编辑器、外部脚本、非合作进程或恶意程序的写入**；本功能不是系统级沙箱。操作者依旧必须信任本地仓库。中断的自动 OS 操作锁随进程退出释放；人工预留锁不会自动失效或被抢占。
- 无 Git 仓库、非根目录或损坏的 Git 元数据会被明确区分。Git 工作树子目录不能以“普通项目”方式绕过跨树保护。
- 中断恢复默认**只读诊断**，只有显式 `--approve` 才可能修改源码或 `.ai` 状态。恢复前验证路径、哈希和历史提交；出现新的用户编辑、暂存区残留或 Git HEAD 冲突会停止。
- 单文件原子替换**不等于多文件操作原子性**。崩溃后留下的 `prepared` 记录需要手动审查；通过重新校验后才可回滚。

## 2. 仓库健康与预留锁

```bash
python fullstack.py repo-readiness --project /absolute/path/to/trusted-repo
python fullstack.py audit-repo --project /absolute/path/to/trusted-repo
python fullstack.py worktree-lock status --project /absolute/path/to/trusted-repo
# 人工预留整个 Git 工作树组（显示一次本地释放令牌，请勿共享/记录到 CI）
python fullstack.py worktree-lock acquire --project /absolute/path/to/trusted-repo --approve
```

使用人工预留令牌后，已有代码修改脚本与本地 Git 操作可添加 `--worktree-token <token>`，例如：

```bash
python -m orchestrator.workflow apply --project /absolute/path/to/trusted-repo --proposal plan.json --approve --worktree-token <token>
python -m orchestrator.git_collab commit --project /absolute/path/to/trusted-repo --change-id <change-id> --message 'Fix reviewed behavior' --approve --worktree-token <token>
```

释放预留锁（即使 OS 临时操作锁已在进程退出后释放）：

```bash
python fullstack.py worktree-lock release --project /absolute/path/to/trusted-repo --token <token>
```

## 3. 恢复中断的源码修改

`workflow.apply` 将备份和目标 SHA-256 持久化为 `prepared` 后才开始逐个写文件。若进程中断，文件可能有些是旧内容，有些是目标内容。先只读诊断：

```bash
python fullstack.py recover prepared --project /absolute/path/to/trusted-repo --change-id <change-id>
```

检查返回的 `files[].state` (`before` / `after` / `drift`) 和 `safe_to_restore`。只在审查确认后：

```bash
python fullstack.py recover prepared --project /absolute/path/to/trusted-repo --change-id <change-id> --approve
```

只有**每个文件都是可验证的旧/目标内容**时，才会按反向顺序回退为原内容，生成文件则删除，并将变更标记为 `aborted`。若用户随后编辑了文件或备份损坏，则拒绝覆盖；需人工处理。重启后可以重新诊断，不会未经确认自动删除文件。

## 4. 恢复中断的本地 Git 提交

在第一次 `git add` 之前记录提交意图，包括基线 HEAD、分支、提交消息、审核文件哈希和测试报告摘要。若程序退出在 `git commit` 与状态更新之间：

```bash
python fullstack.py recover commit --project /absolute/path/to/trusted-repo --change-id <change-id>
```

可能出现：

- `not_committed`：当前 HEAD 仍是基线，且无暂存更改。批准后只清除“未完成提交”的标志，**不会提交或回退源码**。
- `committed_unrecorded`：HEAD 为基线的直接后继，提交消息、目标文件内容、工作区与报告均吻合。批准后只补全 `committed` 状态和提交 SHA，**不会再次提交**。
- 如果 Git 暂存区仍有内容、分支或父提交变化、提交消息/代码摘要不符、报告被篡改，工具拒绝自动恢复。

确认后可使用：

```bash
python fullstack.py recover commit --project /absolute/path/to/trusted-repo --change-id <change-id> --approve
```

当人工预留锁存在时，两种恢复的批准命令均需携带 `--worktree-token <token>`。

## 5. 可重复验证

```bash
python -m unittest tests.test_v46 -v
python -m unittest tests.test_v45 tests.test_workflow tests.test_v43 -q
python fullstack.py verify --profile smoke --execute
python examples/v43-repo-demo/run_demo.py --execute-tests --rounds 3
```

上面的项目测试**只适用于可信来源的代码**；`tools/run_checks.py` 和执行器不是安全沙箱。V4.6 没有真实使用远程 GitHub 账号、真实 CI 授权、生产部署或外部 LLM 服务进行集成验证，详见 `RELEASE_VALIDATION_V4.6.md`。
