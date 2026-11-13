# V4.8 跨平台 CI 与可重复发布工程

本轮保留原有 144 个 Skill，不把代码测试变成自动写入或自动部署。所有真实 GitHub 操作都必须由仓库所有者把工作流提交到其 GitHub 仓库后自行触发。

## 1. 固定工具链

`ci/toolchain.json` 规定 CI 为 Python **3.11**、Node.js **22**、TypeScript **5.9.3**。Python 核心运行工具使用标准库，无额外 pip 依赖。可以检查当前设备：

```bash
python tools/toolchain_v48.py --component python
python tools/toolchain_v48.py --component node --component typescript
```

本地版本和 CI 目标版本不同会报告不一致，但不代表原来工具在其他 Python/Node 版本一定不能工作。CI 安装 `typescript@5.9.3` 并检查版本；目前尚未提供 npm 完整性 lockfile，GitHub Actions 仍使用 `@v4` 等标签而不是不可变完整 SHA，不应声称供应链已经做到完整可复现。

## 2. 跨平台验收与证据

```bash
python fullstack.py ci-plan
python tools/ci_release_v48.py plan
# 以下命令在相应可信本地环境执行固定随包测试；需明确授权
python tools/ci_release_v48.py run --suite core --execute \
  --output benchmarks/reports/ci_v48_linux_core.json
```

Linux 必须提交 `smoke/core/analysis/platform/collaboration/locks` 六份报告；Windows 和 macOS 各需 `locks` 一份。每份报告包含 schema、运行 ID、尝试次数、提交 SHA、源文件哈希、测试组结果和内部报告哈希。所有报告均须来自同一工作流尝试。总数是八份；有任意缺失或内容不一致，汇总器以失败退出，**不会填补缺失平台的数据**。

CI 工作流的 `aggregate` 作业使用 GitHub Actions 官方下载工件动作获取同次运行的八份 JSON，并执行：

```bash
python tools/ci_release_v48.py aggregate \
  --folder benchmarks/reports/collected \
  --expected-sha "$GITHUB_SHA" \
  --run-id "$GITHUB_RUN_ID" \
  --attempt "$GITHUB_RUN_ATTEMPT"
```

**证据可信边界**：校验哈希仅说明内容未在未更新哈希的情况下被更改；报告可以被重新生成，并非数字签名或官方平台认证。实际的身份与运行上下文仍需要在已授权的 GitHub 仓库内检查 GitHub Actions 的工件来源、工作流权限和提交信息，才能作为真实 CI 的操作证据。本地合成报告仅用于契约单元测试，不得引用为真实跨平台通过。

## 3. 可重复 ZIP 打包与验证

```bash
# 先预览，不创建文件
python fullstack.py release-package --output /tmp/ai-fullstack-dev-skills-v4.8.zip
# 明确批准打包；目标目录必须已经存在且文件不得已存在
python fullstack.py release-package --output /tmp/ai-fullstack-dev-skills-v4.8.zip --execute
# 校验归档中的每个文件与 RELEASE_MANIFEST_V4.8.json
python fullstack.py release-package --verify /tmp/ai-fullstack-dev-skills-v4.8.zip
sha256sum /tmp/ai-fullstack-dev-skills-v4.8.zip
```

打包排除 `.git`、`.ai`、缓存、数据库及 `benchmarks/reports/` 等运行状态。归档采用固定文件顺序、时间戳和权限，生成内部 `RELEASE_MANIFEST_V4.8.json` 和外部 `.zip.sha256` 校验文件。验证检查文件列表、体积与 SHA-256，并拒绝路径穿越、重复条目与符号链接。**哈希不等于签名**，分发后若要证明来源，需要独立可信签名或平台的发布证明。

## 4. CI 发布候选包

GitHub Actions 只在八份报告的聚合关卡通过后创建 release candidate ZIP 并上传工件；**不会发布 GitHub Release、推送代码、合并 PR 或部署**。Windows/macOS 工作流配置不代表已经实际在那两个系统运行成功。

## 5. 未完成的生产级能力

真实多平台 GitHub Actions 运行、固定 Actions 的完整提交 SHA、npm 供应链锁定、签名和 SLSA 来源证明、真实业务仓库长时间稳定性、恶意代码执行隔离均仍待实际环境中的后续验证。
