# V3.7 发布验证记录

## 环境
- Python 3.13.5（当前执行环境）；Node.js 22.16.0；TypeScript 编译器：本地全局安装（随工具目录不捆绑）。
- CI 另外明确配置 Python 3.11、Node 22、TypeScript 5.9.3；配置已更新，**未在真实 GitHub Actions runner 上执行 CI**。

## 实际执行并通过的验证

| 检查 | 结果 |
|---|---|
| Python 主工具与工作流回归 | **206/206** 通过（V3.6 原有 185 + 新增 21） |
| 路由基准 | Skill **28/28**、模式 **28/28** |
| Skill 目录与索引 | 保留 **144** 个 Skill；审计 passed，issues=0，warnings=0 |
| V3.5 固定检索与失败分类评测 | 10/10 检索命中，原始固定分类样例指标 100% |
| V3.6 固定 AST/失败路径评测 | **14/14** 符号、**8/8** 路径 |
| V3.7 四项目固定基准 | **6/6** 跨语言符号、**5/5** 测试影响 |
| Python Inventory fixture | unittest **1/1** |
| Python Notes fixture | unittest **1/1** |
| Todo API 示例 | unittest **11/11** |
| JavaScript CommonJS fixture | `node --test` **1/1** |
| TypeScript fixture | `tsc --noEmit` 成功；编译输出由 `node` 实际运行成功 |
| 离线双轮修复 | 第一轮测试失败、第二轮通过、恢复原始内容；实际演示成功 |
| 增量缓存 | 首次解析 5 个文件，随后复用 **5/5**；同 mtime 内容改动和文件删除由单元测试覆盖 |
| 编译 / Catalog | Python compileall、Catalog 生成检查成功 |

## 变更安全回归
- 源码解析默认只读；显式 `--save-cache` 才保存元数据到 `.ai/cache/`，缓存排除在版本控制之外。
- 覆盖软链接跳过、敏感文件跳过、缓存软链接拒绝、文件容量上限、JS/TS 解析器缺失明确报错、缓存哈希失效、未知变更路径与动态/未解析导入的全量测试提示。
- `orchestrator/agent.py --multilang-hints` 只产生本地提示，不扩展显式选择的模型上下文，也不写源码。
- 修复继承的测试 fixture 假设：项目初始化依旧默认禁用检查；只有受信任的演示 fixture 显式启用测试。

## 测试范围与限制
- 四个项目都是**随仓库提供的透明教学样例**；没有声称在未知、真实大型第三方仓库上达标。
- Python 静态 AST 和 TypeScript compiler AST 不等同完整 LSP 或运行时调用分析。动态导入、复杂包别名、依赖注入和 tsconfig 路径映射存在盲区。
- 推荐测试集合仅用于开发阶段优先运行；**合并或发布前必须完成全量测试**，不能因为 `full_suite_required=false` 就跳过。
- 未运行真实 Docker 容器、真实 GitHub 远程 PR、真实付费模型服务；CI 只更新配置但尚无平台端成功记录。
- 一个串行完整验证命令曾触发时间限制；随后剩余验证均拆分单独执行并获得成功结果。未将超时步骤视为通过。
