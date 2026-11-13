# GitHub 发布教程（中文） · V5.0

本教程面向**首次将本项目发布到公开 GitHub 仓库**的用户。上传前应核实源码版权和第三方素材许可；本指南不代替法律意见。

## 一、上传前检查

- [ ] 使用本工具包的源码文件夹作为仓库根目录，不要直接把 ZIP 当作唯一的仓库内容。
- [ ] 把 `README.md` 放在根目录，确认相对链接指向存在的文件。
- [ ] 保留 `CHANGELOG.md`、`docs/QUICKSTART_CN.md` 和 `docs/ENGINEERING_V5.0.md`。
- [ ] **核实 `LICENSE`**：原始 V5.0 的 MIT 文本较简短且版权声明未写权利人。发布前请由真实版权所有人补齐和核对适当的完整许可文本；不要擅自为其他作者的资产授予 MIT 许可。
- [ ] 审核 `skills/`、`examples/` 与第三方文件的再分发许可。
- [ ] 检查 `.env`、令牌、测试日志、个人信息和 `.ai/` 私有状态，确保未被追踪。
- [ ] 不要误标为“生产级安全沙箱”或“自动完成所有编程任务”。
- [ ] 首发版本为 V5.0，`RELEASE_VALIDATION_V5.0.md` 明确描述本地验证边界。

## 二、创建 GitHub 仓库

1. 登录 GitHub，选择 **New repository**。
2. 建议名称：`ai-fullstack-dev-skills`；简介：`An AI-assisted full-stack engineering toolkit with 144 skills, governed code changes, testing, and release management.`
3. 选择 Public 或 Private。若要公开，请先完成许可、隐私、依赖与源码检查。
4. **不要勾选自动创建 README、.gitignore 或 License**，以免与本地文件冲突。
5. 创建成功后复制 GitHub 仓库 HTTPS 地址。

## 三、推送源码（Windows PowerShell / Git Bash / macOS / Linux）

在**包含 `fullstack.py` 的目录**执行，替换 `YOUR_ACCOUNT`：

```bash
git init
git branch -M main
git add .
git status --short
# 审核暂存内容，确认没有密钥/业务数据
git commit -m "Release v5.0 source and documentation"
git remote add origin https://github.com/YOUR_ACCOUNT/ai-fullstack-dev-skills.git
git push -u origin main
```

如果该目录已有 Git 仓库，不要重复初始化并覆盖已有的 `origin`。应先运行 `git status` 和 `git remote -v`，核实再操作。GitHub 需要你自己的账号授权/凭据。本工具不替你创建或推送远程仓库。

## 四、发布 V5.0 Release

1. 进入仓库的 **Releases → Draft a new release**。
2. Tag：`v5.0.0`（建议使用语义版本标签；软件仍显示 `5.0`），Target：`main`。
3. Title：`AI Fullstack Dev Skills V5.0`。
4. Release notes：复制 [`RELEASE_NOTES_V5.0.md`](../RELEASE_NOTES_V5.0.md) 的内容。
5. 上传**原始发行包** `ai-fullstack-dev-skills-v5.0.zip`，以及匹配的 `.sha256`、`.provenance.json`、`.sbom.json`。请确保这些侧车文件确实来自同一个原始发行包。
6. 先保存为 Draft，检查附加文件和描述无误后再发布。

**很重要：** 为 GitHub 仓库改进 README/文档后得到的仓库源码快照，与最初发行的 `ai-fullstack-dev-skills-v5.0.zip` 可能不是完全相同的字节内容。**不要用原始 ZIP 的 SHA-256 去验证重新打包后的源码 ZIP**；也不要把为原始 ZIP 制作的未签名来源记录伪称为新增 GitHub 仓库快照的构建证明。两者应分别标注。

## 五、发布后检查

- GitHub 仓库首页可以正常阅读 README，链接不报 404。
- 在 **Actions** 页面查看真实 CI 结果，留意 Linux/Windows/macOS 是否全部执行且通过；不要只凭 YAML 判断通过。
- 确认 Release 中的 ZIP 与 `.sha256` 匹配。
- 确认公开源码不含密钥、生产数据库或敏感日志。
- 检查 GitHub Issues、Releases、License 显示是否符合预期。

## 六、后续维护

每个新版本更新 `CHANGELOG.md` 和详细版本日志；配合 Release tag / release notes 发布。必要时使用 V5.0 生命周期工具做本地升级/回滚。若未来要做发行签名，应先建立可验证、可信的发布者密钥与流程。

参考官方文档：
- https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
- https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
