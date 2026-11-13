# 中文使用教程 · V5.0

本教程面向第一次下载工具包的开发者。**V5.0 不是无需配置即可自主开发所有软件的 AI 产品**，而是包含 144 个技能文件、Python CLI、受控代码工作流与工程工具的可扩展工具包。

## 1. 环境准备

- Python 3.10 或以上（建议 3.11），通过 `python --version` 查看。
- 推荐安装 Git，通过 `git --version` 查看；只有 Git 功能必须使用 Git。
- JS/TS 符号分析和示例需要 Node.js、TypeScript；发布 CI 的目标版本为 Node.js 22 / TypeScript 5.9.3。
- OpenSSL、clangd、Docker、GitHub CLI 属于按功能安装的可选依赖。普通命令无需 API Key。

Windows：可使用 PowerShell 运行 `py -3 fullstack.py ...`；macOS/Linux：通常运行 `python3 fullstack.py ...`。下面统一写 `python`，请按本机命令替换。

## 2. 直接使用解压源码（最简单）

1. 下载 V5.0 源码 ZIP 并解压。
2. 进入包含 `fullstack.py` 的目录：

```bash
python fullstack.py --version
python fullstack.py doctor
python fullstack.py --help
```

3. 根据任务查看技能路由：

```bash
python fullstack.py route --task "开发一个用户注册和登录系统"
```

4. 查看供应链规则、测试计划：

```bash
python fullstack.py supply-chain audit
python fullstack.py release-matrix --shard all
```

`release-matrix` 默认不执行测试。只有对随包代码来源有信任时才使用：

```bash
python fullstack.py release-matrix --shard all --execute
```

## 3. 可视化控制台

```bash
python fullstack.py dashboard --project project --port 0 --open
```

使用终端输出的本机令牌地址访问控制台。看板只读，不修改仓库或执行 Git 提交。不要转发令牌，不要将其反向代理到公网。

## 4. 使用 V5.0 的独立版本管理（进阶）

适合计划长期更新 V5.1、V5.2 的用户。**不要把已有业务项目目录作为 `--home`**。应另建一个空的安装目录，并将业务文件存放在其 `workspace/` 子目录。

从独立可信来源核对发布 ZIP 的 SHA-256 后：

```bash
python fullstack.py lifecycle plan --home /absolute/empty-install-home --archive /absolute/v5.0.zip --expected-sha256 YOUR_TRUSTED_SHA256
python fullstack.py lifecycle install --home /absolute/empty-install-home --archive /absolute/v5.0.zip --expected-sha256 YOUR_TRUSTED_SHA256 --approve
python fullstack.py lifecycle status --home /absolute/empty-install-home --integrity
```

升级时用 `lifecycle upgrade --approve`；回滚使用 `lifecycle rollback --approve`。各项参数与 Windows 路径示例请参阅 [详细工程教程](ENGINEERING_V5.0.md)。回滚仅切换软件版本，**不会自动回滚业务数据库和线上部署**。

## 5. 与 AI 编程工具配合

阅读 `AGENTS.md`、`CLAUDE.md`、`docs/AGENT_INTEGRATION.md` 和 `SKILLS_INDEX.md`。若启用远程模型，应逐文件确认发送内容；模型生成的 JSON 提案需要预览、批准、测试，不能自动获得写入权限。

## 6. 常见问题

**Q: 需要付费 API 吗？** 不需要即可查看、路由和运行本地工具。远程 AI 模型功能需要自行配置服务与授权。

**Q: 可以直接执行未知仓库测试吗？** 不建议。测试代码可能执行任意脚本，工具包不是安全沙箱。

**Q: GitHub Actions 绿色了吗？** 仓库包含工作流定义，但正式 V5.0 发布记录没有线上跨平台执行证据。推送后应检查 Actions 页面。

**Q: 为什么 TypeScript CI 与本机版本不一样？** 发布目标是 TypeScript 5.9.3，本地原验证环境使用过 5.8.3；应以你的实际 `npm ci` 和 CI 结果为准。

**Q: 怎么汇报问题？** 请附操作系统、Python 版本、已脱敏的命令和报错，避免提交令牌、个人信息和业务源码。
