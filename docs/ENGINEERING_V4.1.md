# AI Fullstack Dev Skills V4.1 — 本地可视化项目控制台

## 定位

V4.1 在 V4.0 命令行入口基础上新增**本机只读 Web 仪表盘**，不依赖前端框架、Python 第三方 Web 框架或公网服务。保留所有 144 个 Skill 及 V2–V4.0 的 CLI、审批、修复、Git 和测试模块。

**功能仅为查看，不能通过 Web 页面创建任务、审批源码、执行测试、提交或推送 Git、调用模型、安装插件。** 它不是互联网可访问的云服务，也不能代替工程日志审计、代码审查及独立测试环境。

## 1. 启动

要求 Python 3.10+，无须 `pip install`。在解压后的工具包根目录：

```bash
# 预先建立项目状态（仅初次需要）
python fullstack.py project init --project project

# 启动本地网页，默认使用 127.0.0.1:8765
python fullstack.py dashboard --project project

# 自动选择空闲端口，且显式打开本地浏览器
python fullstack.py dashboard --project /path/to/your/project --port 0 --open
```

程序会在终端打印一次**含随机访问令牌**的本地链接，例如 `http://127.0.0.1:8765/?token=<随机令牌>`。浏览器通过令牌完成登录后，URL 会跳转为不含令牌的 `/`，后续浏览使用 HttpOnly、SameSite=Strict 的会话 Cookie。请勿分享原始链接。关闭终端上的进程（Ctrl+C）即停止本地服务，重启会使用新令牌。

端口已占用时会拒绝启动，可用 `--port 0` 自动选择。此服务仅绑定 IPv4 回环地址 `127.0.0.1`，**没有对局域网或公网开放的参数**。

## 2. 页面

| 页面 | 读取的信息 | 不提供的操作 |
|---|---|---|
| 项目总览 | 任务统计、完成比例、最近报告、质量摘要 | 不创建或更新任务 |
| 任务管理 | `.ai/task_state.json`，验收报告哈希检查 | 不标记任务为已完成 |
| 测试与验收 | `.ai/reports/*.json` 的状态/数量/时间 | 不运行项目测试，不读取输出给浏览器 |
| AI 修复记录 | `.ai/loops/*/state.json` 的汇总统计 | 不发送源码给模型，不自动进入下一轮 |
| 代码变更 | `.ai/changes/*/manifest.json` 的 ID/文件计数/状态 | 不展示 diff/备份，不恢复或批准修改 |
| Git 仓库 | 本地当前分支、HEAD、`git status` 的部分文件状态 | 不执行 Git add/commit/checkout/push/merge |

网页每 30 秒按需读取一次数据，也可以点击右上角的「刷新数据」。未运行任何任务时显示空状态，不伪造示例指标。项目未执行 `project init` 时可查看空态，不会暗中创建 `.ai` 目录。

> 验收证据显示为「已核验」，表示文件指纹与任务保存的 SHA-256 一致；它不代表测试本身一定正确，也不代表最终产品已通过安全审计。人工验收单独标记；不展示人工理由正文。

## 3. 隐私及访问边界

- 本地随机令牌、严格 Host 头校验、无 CORS 放行、无网页写接口、CSP、no-store、防嵌入/防嗅探响应头。
- 数据文件读取设置数量与大小上限；拒绝 `.ai` 为软链接、拒绝跟随任务和报告软链接；遇到损坏或超大记录会警告或跳过。
- 向浏览器返回的 JSON **不包含**项目源码、补丁 diff、备份、测试 stdout/stderr、模型输入、访问密钥或人工验收原因。任务标题、项目绝对路径和 Git 文件名仍属于**项目元数据**，请避免在共享设备上使用。
- 读取 Git 状态会启动本地 Git 可执行程序，但不执行项目测试、Git hooks、远程 fetch 或用户代码；Git 状态查询设置超时，并禁用 fsmonitor 和 hooks。只应在信任的本地工作区使用。
- 本地 HTTP 不加密；它依赖回环地址和会话令牌，不适合转发端口、代理到公网、多人协作或远程部署。其他本机进程理论上可以尝试本机端口，且浏览器扩展仍可能访问页面；敏感环境需要更严格的独立隔离。
- 刷新页面不会写业务文件；它不是**安全沙箱**。对不可信的仓库不要直接执行测试或 LSP。

## 4. 其他操作继续用 CLI

```bash
python fullstack.py project status --project project
python fullstack.py check --project project           # 只预览
python fullstack.py check --project project --execute --save-report  # 审查可信项目后显式执行
python fullstack.py verify --profile smoke --execute  # 工具包固定本地验收
```

对于带审批的代码修改、修复循环及 Git 变更仍使用 V3.x 原有命令行工具。V4.1 不改变任何高风险审批规则。

## 5. 自测

```bash
python -m unittest discover -s tests -p 'test_v41.py' -v
node --check dashboard/static/app.js
python fullstack.py dashboard --help
```

以上单元测试包括真实本地 HTTP 请求、令牌登录、禁止写操作、恶意 Host、软链接、证据指纹异常、Git 只读、无敏感正文外传。浏览器前端通过 Chromium 离线注入数据验证了任务筛选与渲染；无真实远程模型、云端 GitHub 或跨设备访问测试。
