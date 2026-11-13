# V4.2 工程指南：真实样例验收与长期运行稳定性

## 本版解决的问题

V4.1 的任务统计把首页先取出的前 300 项当作项目总量，无法在任务持续增长时准确显示整体进度；大量报告只扫描到前 500 个目录条目，可能忽略后续新增的报告。V4.2 将**任务总数与状态分布**改为基于整个有效任务状态文件计数，**任务列表**仍展示最近更新的至多 300 项；报告与变更会在有界目录扫描范围内按修改时间选取最近 60 条。

新增 `coverage` 字段记录：任务总数、列表展示数量、报告/变更展示数量、证据检查任务数。页面会明确提示截断，搜索与筛选只作用于当前已展示的任务。**报告的通过率与变更数量是最近 60 条展示样本的统计，不等于全项目历史总量。** 证据完整性检测也是展示样本，不应据此认定未展示任务的证据均有效。

若修复会话目录数超过 400，修复统计标为不可用，并给出警告，而不是误显示零次。报告/变更目录单次扫描最多 10,000 项，达到扫描上限会告警；在极大项目中需要额外的索引或分页服务。

## 1. 可重复的压力测试（默认完全临时）

要求 Python 3.10+；不需要第三方 Python 依赖。

```bash
# 自己生成临时项目、900 项合成任务、120 份合成报告和 80 条合成修复记录
python tools/stability_v42.py --tasks 900 --reports 120 --loops 80 --reads 10

# 可选：只读检查一个既有项目，不写项目文件，不运行项目代码
python tools/stability_v42.py --project /absolute/path/to/project --reads 5
```

前者在系统临时目录中生成数据，循环读取投影结果，再在**仅限临时项目内**并发进行原子任务状态更新和看板读取。测试结果包含本机观测到的最小/中位/最大延迟、统计一致性和并发错误。合成报告带有 synthetic 标记，**不是实际运行后的验收证据**。

传入 `--project` 时不生成记录、不开启并发写入，也不允许 `--output`；这一模式只读取该项目已有状态并记录延迟。浏览器/HTTP 控制台本身仍需 `python fullstack.py dashboard --project ...` 单独启动。

## 2. 在随包实际项目上验证证据闭环

```bash
# 默认只预览检查，不运行测试
python examples/v42-reliability-demo/run_demo.py

# 明确授权后运行随包 Todo 项目的 Python API 测试
python examples/v42-reliability-demo/run_demo.py --execute-tests
```

第二条命令会复制随包 `examples/runnable-todo` 到临时目录，在副本中初始化 `.ai` 状态、创建任务、运行 Python unittest、保存检查报告、用 SHA-256 关联任务证据、再从 V4.2 仪表盘只读投影读取最终状态，最后清理临时项目。

**执行 Python 单元测试就是执行 Python 代码**。此演示只应用于可信的随包项目；不应将相同的检查权限无审查地授予不可信仓库。该演示验证了实际测试执行与验收关联，不代表外部大型仓库或生产部署已验证。

## 3. V4.2 新增数据结构与兼容性

- `dashboard.snapshot.snapshot()` 仍输出原来的 `stats`、`tasks`、`reports`、`changes`、`loops`、`git` 和 `warnings`。新增 `coverage`；`stats.tasks` 和 `stats.by_status` 改为真实有效任务总数。
- 单个任务状态文件允许读取的上限从 512 KB 提升至 12 MB，且读取结果不向浏览器暴露验收原因、模型提示词等隐私正文。
- 若项目包含超过 300 个任务，列表取最近更新者，原有任务不会删除或改写；看板每 30 秒重新读取本地文件。
- 通过 `os` 文件原子替换写入的任务状态可被并发读取；并发读取期间报告/变更文件被移除时会跳过，避免整个看板因单个条目出现异常。
- `loops.available` 表示修复统计是否成功读取。`false` 表示超限或不可用，**不能解读为 0 次修复**。
- 看板默认仍仅绑定 `127.0.0.1`、使用随机令牌、只接受 GET，不能通过网页修改源码、运行测试或 Git 提交。

## 4. 回归检查

```bash
python -m unittest tests.test_v41 tests.test_v42 -v
node --check dashboard/static/app.js
python tools/audit_catalog.py
python tools/benchmark_router.py
python fullstack.py verify --profile smoke --execute
```

本轮代码未实现云端协作、无监督代码修改、数据库迁移、全量历史查询或自动分布式压力测试。跑在本地合成数据上的毫秒数只是观察结果，不构成性能 SLA；测试数量不等同真实项目上的可靠性保证。
