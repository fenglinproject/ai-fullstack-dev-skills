# Changelog · AI Fullstack Dev Skills

> 这是 GitHub 首页使用的**版本概要**，对应具体代码改动请查看各版本的 `CHANGELOG_V*.md`。已完成的本地验证不应被解释为真实远程 CI、生产安全认证或第三方签名。

## [V5.0] — 2026-11-13

**Product lifecycle & installation safety**
- 新增侧并版本安装管理，支持安装预览、SHA-256 校验、人工授权升级、回滚和独立 `workspace/`。
- 提供版本完整性启动校验、可选公钥签名核验、发布材料清单与受控迁移入口。
- 继续保留 144 个专业 Skill 以及历史开发审批和 Git 工作流。

详见 [CHANGELOG_V5.0.md](CHANGELOG_V5.0.md) · [使用教程](docs/ENGINEERING_V5.0.md)

## [V4.9] — 2026-11-13

**Supply-chain hardening**：将 GitHub Actions 引用固定为提交 SHA，添加 TypeScript 锁文件、SBOM、未签名来源元数据、可选数字签名及发行安全检查。详见 [CHANGELOG_V4.9.md](CHANGELOG_V4.9.md)。

## [V4.8]

**Release engineering**：跨平台 CI 验收配置、要求多平台证据一致的聚合关卡、确定性 ZIP 打包与逐文件哈希。详见 [CHANGELOG_V4.8.md](CHANGELOG_V4.8.md)。

## [V4.7]

**Test stability**：独立进程的完整回归矩阵、时间预算、结构化证据和故障注入测试。详见 [CHANGELOG_V4.7.md](CHANGELOG_V4.7.md)。

## [V4.6]

**Concurrent write safety**：跨 Git worktree 操作锁，中断文件修改和 Git 提交的受控恢复。详见 [CHANGELOG_V4.6.md](CHANGELOG_V4.6.md)。

## [V4.5]–[V4.3]

**Git collaboration and trust**：已有 Git 仓库接入预检、本地 CI 检查线索、worktree 协调、证据与提交基线绑定、连续本地 Git 验证。详见 [V4.5](CHANGELOG_V4.5.md)、[V4.4](CHANGELOG_V4.4.md)、[V4.3](CHANGELOG_V4.3.md)。

## [V4.2]–[V4.0]

**Developer experience**：统一 `fullstack.py` CLI、本机只读 Web 看板、稳定性采样与可运行示例验收。详见 [V4.2](CHANGELOG_V4.2.md)、[V4.1](CHANGELOG_V4.1.md)、[V4.0](CHANGELOG_V4.0.md)。

## [V3.9]–[V3.5]

**Code intelligence**：LSP 客户端与项目配置静态解析、Monorepo 依赖图、Python/JS/TS 符号索引、上下文选择、故障分类和固定离线基准。详见各版本 `CHANGELOG_V3.x.md`。

## [V3.4]–[V3.0]

**Governed coding workflows**：AI 修改提案、差异预览、人工审批、测试验收、回退、多轮修复、Git 审查、局部隔离测试适配与项目质量记录。详见 `CHANGELOG_V3.md` 及后续版本。

## [V2.1]–[V2.0]

**Skill architecture**：保留 144 个 Skill，修复路由引用、共享规则、调整风险门禁，加入初代任务管理、测试执行与示例。详见 [V2](CHANGELOG_V2.md) 和 [V2.1](CHANGELOG_V2.1.md)。

---

> 注意：这里的发布日期仅对在原始更新日志中记录了明确日期的版本给出；其余版本不擅自补充日期。
