# V4.6 发布验证报告

日期：2026-11-10；范围：从 V4.5 正式 ZIP 重建的 V4.6 工作目录。原始 V4.5 ZIP 未改变。

## 结果总览

| 验证 | 结果 | 说明 |
|---|---|---|
| Python 工具 / 工作流回归 | **354 / 354 通过** | 六组独立运行，全部明确退出码 0；不是一次性全量单命令通过 |
| V4.6 新增测试 | **15 / 15 通过** | 含真实 linked worktree 跨进程锁竞争、令牌、部分写入、Git 提交中断与文件漂移 |
| Skill 目录审计 | **144 Skill / 0 issues** | 16 类别、30 个主技能；`tools/audit_catalog.py` |
| 路由基准 | **28 / 28** | `tools/benchmark_router.py` |
| Smoke 工程验收 | **4 / 4** | catalog / router / v4-unit / Todo API，实际执行通过 |
| 随包独立 Git 工作流 | **3 / 3 本地提交** | 3 次测试验收、3 项完成任务，最后仓库干净 |
| Node.js 示例 | **1 / 1** | `node --test` 实际通过 |
| JavaScript 语法 | **通过** | `node --check dashboard/static/app.js` |
| TypeScript 类型检查 | **通过** | `tsc --project benchmarks/projects/ts-workspace/tsconfig.json --noEmit` |
| 目录与索引一致性 | **通过** | `tools/sync_catalog.py --check` |

Python 354 项分组如下：

1. `test_agent_bridge test_loop test_loop_cli test_orchestrator test_v21 test_workflow_demo`：85 项通过。
2. `test_v33 test_v34 test_v35 test_v36 test_v37 test_v38 test_v39`：143 项通过。
3. `test_v40`：13 项通过。
4. `test_v41 test_v42`：23 项通过。
5. `test_v43 test_v44 test_v45 test_v46`：69 项通过。
6. `test_workflow`：21 项通过。

**历史回归执行说明：** V4 系列多个模块合并执行曾触发运行超时。已按上述单独分组逐项完成复核；超时不计入通过结果。没有在本次构建中确认单命令 `python -m unittest discover -s tests` 一次性全部执行通过。

## 真实演练范围

- 在临时本地 Git 仓库和 linked worktree 中，观察两个不同进程使用同一个 Git common-dir 操作锁，竞争时拒绝第二个写入者。
- 通过 V4.5 人工预留令牌验证无授权拒绝写入、有匹配令牌后允许受控操作。
- 利用持久化 `prepared` 记录模拟部分文件写入、创建文件未完成、用户额外编辑、损坏备份；仅在哈希完全匹配时回退。
- 使用一次实际完成的本地 Git 提交、在记录最终化前抛出模拟异常；再次只读识别该提交，并在人工批准后补录相同 SHA（不重复提交）。
- 对已有 Git 暂存文件、测试报告篡改以及不安全锁文件执行负面测试。
- 运行随包可信 `examples/v43-repo-demo/run_demo.py --execute-tests --rounds 3`，成功生成 3 个连续本地提交，无远程操作。

## 未覆盖与限制

- 未连接用户的真实生产仓库，未验证真实 GitHub CI 账号、远程 PR、自动 merge / deploy。
- 没有运行 Docker 沙箱或远程 LLM 的实际调用；测试环境不构成代码执行沙箱。
- Git OS 锁仅对该工具包参与的入口生效，不能强制外部编辑器/Git/恶意进程协同。
- 测试主要基于本地可信示例、临时 Git 仓库及故障注入，不构成跨设备、生产级故障恢复证明。
- `.ai/` 元数据与 SHA-256 是本地一致性保护，不是不可篡改的远端证明。
