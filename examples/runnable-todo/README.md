# 本地可运行全栈示例：任务清单

使用 Python 3.10+ 标准库、SQLite、HTML/CSS/JavaScript，**无需下载依赖**，可在离线环境测试。原有四个示例仍保留为规范参考；本示例用于真实运行验证。

## 快速开始

在本目录运行：

```bash
python backend/server.py
```

打开 `http://127.0.0.1:8765`。可注册账号、登录、增删任务、完成任务；不同账号数据隔离。

## 测试

```bash
python -m unittest discover -s tests -v
```

或从技能库根目录执行：

```bash
python tools/run_checks.py --project examples/runnable-todo --run
```

## 安全边界

这个示例展示最基本的服务端权限校验、参数化 SQL、PBKDF2 加盐密码和 CSP，但**不是生产认证实现**。Token 只在本地进程内、无持久化、无失效/撤销策略，未实现限速、邮件验证、CSRF/SameSite Cookie、HTTPS 终止、生产日志审计等。HTTP 服务只绑定 127.0.0.1。不要直接部署到公网。

- API 接口文档见 `docs/API.md`
- 代码在 `backend/`、`frontend/`；测试在 `tests/`
- 数据库存储在本示例目录下的 `todo.sqlite3`，可停止服务后删除以重置本地演示数据
