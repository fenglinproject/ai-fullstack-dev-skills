# V4.8 发布工程与跨平台 CI 验收

- 新增 `tools/ci_release_v48.py`，对固定 CI 测试组生成带 SHA-256 的结构化执行记录，汇总时强制要求 **同一 Git SHA、run ID、attempt** 下的八份记录：Linux 的 smoke/core/analysis/platform/collaboration/locks，以及 Windows/macOS 的 locks。无证据、失败、未执行、重名文件、报告哈希变化或历史源码哈希不匹配均拒绝通过。
- `.github/workflows/test.yml` 增加显式聚合关卡。仅聚合成功后运行独立打包任务，整个工作流没有远程发布、合并或部署操作。
- 新增 `tools/package_release_v48.py`，可重复生成固定内容与 ZIP 元数据的发布包，内含逐文件 SHA-256 清单，并生成外部 `.sha256` 校验文件。验证器拒绝目录穿越、重复文件、软链接与不匹配内容。
- 新增 `ci/toolchain.json` 与 `tools/toolchain_v48.py`，CI 明确使用 Python 3.11、Node.js 22、TypeScript 5.9.3。Python 主运行功能没有新增第三方依赖。
- 增加统一 CLI `ci-plan`、`ci-aggregate`、`release-package`，更新发布矩阵覆盖 V4.8 测试模块，并保留全部 144 个 Skill、Git 审批、测试回滚和本地控制台。
- 新增 24 项离线专项测试，覆盖错误证据、漏测平台、包完整性、可重复性和工具链版本检查。

## 边界

CI JSON 与 SHA-256 是**一致性/完整性材料**，不是数字签名，也不能独立证实报告来自 GitHub。真正跨平台通过，必须查看经 GitHub Actions 工作流下载并核查的同次运行记录。当前没有真实 Windows/macOS 的运行回执，不能宣称跨平台已经验证。

TypeScript 安装是明确的版本固定，但目前**没有 npm 完整性锁文件**或 GitHub Actions 的不可变 commit-SHA 固定；本次没有把版本号固定误称为全依赖供应链锁定。
