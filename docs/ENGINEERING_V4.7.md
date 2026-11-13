# V4.7 工程稳定性与发布验收

V4.7 采用 V4.6 的全部 144 个 Skill、人工批准的修改与 Git 提交以及中断恢复机制；本次重点是可信随包测试的**进程隔离、时间预算和可审计性**，而不是加入不受控自动开发能力。

## 1. 四组固定发布验收

```bash
# 只生成计划，不执行代码
python fullstack.py release-matrix --shard all

# 明确授权执行当前工具包自带测试，自动逐个进程运行
python fullstack.py release-matrix --shard all --execute --module-timeout 90 --max-total-seconds 600

# 分组单独执行，避免 CI 单任务长期阻塞
python tools/release_matrix_v47.py --shard core --execute
python tools/release_matrix_v47.py --shard analysis --execute
python tools/release_matrix_v47.py --shard platform --execute
python tools/release_matrix_v47.py --shard collaboration --execute

# 如需存档，输出文件必须是 benchmarks/reports/ 下的全新 JSON 文件
python fullstack.py release-matrix --shard platform --execute \
  --output benchmarks/reports/v47_platform_local.json
```

四个 shard 的测试模块集合由 `tools/release_matrix_v47.py` 定义。启动前要求模块列表和实际 `tests/test_*.py` 精确一致，避免新增测试无声漏掉。每个模块在独立 Python 进程中运行，支持超时和总时长预算。失败、超时与预算不足的模块会分别标记 `failed`、`timeout`、`not_run`。只有所有模块都 `passed` 时，正式执行命令才以退出码 0 结束。未安装的可选依赖可能导致测试跳过；查看报告内容，不要仅以 0 退出码推断所有环境功能都得到覆盖。

这仍然是**本机执行随包 Python 测试**，不是沙箱。没有自动联网、调用模型、访问用户仓库或执行外部仓库脚本。输出包含各模块脚本 SHA-256、实际耗时、Python unittest 报告的测试数量，以及失败时有界截断的诊断尾部。建议按需在受信任机器上运行。

## 2. 受控故障注入

```bash
# 预览将执行什么
python tools/fault_injection_v47.py

# 明确授权，在系统临时目录创建 Git 仓库并运行进程死亡演练
python tools/fault_injection_v47.py --execute
```

实际演练包含：持有 V4.6 的 Git common-dir 操作锁、并发访问被拒绝；操作进程被强制结束后 OS 锁释放；如果平台允许创建软链接，还核对软链接伪装的锁文件被拒绝，受保护的哨兵文件保持不变。

**不保证**能防御未使用此锁的编辑器、直接 Git 命令或恶意本地进程，也**不构成**断电、磁盘损坏或生产分布式事务的恢复证明。

## 3. CI 与平台支持

`.github/workflows/test.yml` 已将测试拆为 `smoke`、四组 `isolated-python`、三个操作系统上的 `cross-platform-locks`。单个模块超时会失败，而不是阻止其他测试组完成；每个 shard 会产生独立的 JSON 验收证据。Linux、Windows、macOS 的 CI 配置不等同于已经在这些系统上执行通过。真实覆盖情况以 GitHub Actions 实际运行记录为准。

## 4. 仍然存在的限制

- 单个测试进程是进程隔离，不是安全隔离。不要对未审查仓库的任意测试运行本工具。
- `subprocess` 失败输出只保留最后一段日志；如需详细调试，应在可信环境单独重现失败模块。
- Unix 下强制结束测试进程组，Windows 下尽力使用系统进程树终止；子进程清理无法保证对恶意进程完全有效。
- CI 工作流尚未通过真实远程 GitHub Actions 运行证明；离线测试通过不能替代生产环境验收。
- 真实 GitHub CI、在线模型、生产仓库及 Docker 隔离不在 V4.7 的本地验收范围内。

详见 `RELEASE_VALIDATION_V4.7.md` 和 `CHANGELOG_V4.7.md`。
