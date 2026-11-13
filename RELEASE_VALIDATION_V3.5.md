# V3.5 发布验证记录

验证范围：本压缩包内 Python 实现、离线基准、随包 Todo API 示例，以及旧版技能路由和目录；该记录不代表外部模型、容器隔离或 GitHub 线上权限已获验证。

## 本地执行结果

| 检查 | 结果 |
|---|---|
| `python tools/sync_catalog.py --check` | 通过，索引一致 |
| `python tools/audit_catalog.py` | 通过：144 个 Skill、30 个主入口、0 个已报告 issue/warning |
| `python -m compileall -q orchestrator tools tests examples/runnable-todo/backend examples/loop-demo` | 通过 |
| `python -m unittest discover -s tests -v` | **166/166 通过** |
| `(cd examples/runnable-todo && python -m unittest discover -s tests -v)` | **11/11 通过** |
| `python tools/benchmark_router.py` | **28/28 Top-1、28/28 执行模式通过** |
| `python tools/benchmark_v35.py --output benchmarks/v35_results.json` | 检索 Recall@3 **10/10**、Top-1 **10/10**、分类 **8/8** |
| `orchestrator/agent.py context ... --auto-context` | 本地真实 CLI 预览通过 |
| `orchestrator/agent.py context ... --auto-context --send-to-model` | 确认拒绝调用，错误退出码 2 |

## 适用范围与限制

- 10 个检索示例来自两个随包工程、8 个分类示例为固定编写的报错文本，**属于小规模、非盲测的离线回归用例**；结果 100% 不能推广到其他项目，不等于真实 AI 编程成功率。
- 上下文检索采用词项与路径启发式，不是 embeddings、AST 全语义依赖分析或语言服务器。自动选取候选文件不能直接授权远程传输。
- 多轮修复中的类别提示是启发式建议；没有自动试验不同修复策略或验证模型效果改善。
- 未使用真实收费模型 API、GitHub 账户、Docker 容器或生产环境，原有人工审批、测试授权和回退规则保持有效。
- 源码和测试输出按不可信数据处理；密钥正则扫描不保证发现所有秘密数据，发送给外部模型前仍要人工核查。

完整使用方法见 `docs/ENGINEERING_V3.5.md`；变更见 `CHANGELOG_V3.5.md`。
