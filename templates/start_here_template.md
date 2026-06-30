# START HERE：项目启动说明

## 1. 项目说明

本项目是：【项目名称】

项目类型：【小程序 / H5 / APP / 后台系统 / 后端服务】

---

## 2. 技术栈

| 模块 | 技术 |
|---|---|
| 前端 |  |
| 后端 |  |
| 数据库 | MySQL 8.x |
| 部署 |  |

---

## 3. 本地环境要求

| 工具 | 推荐版本 | 检查命令 | 用途 |
|---|---|---|---|
| Node.js | 18+ / 20+ | node -v | 前后端运行环境 |
| MySQL | 8.x | mysql --version | 数据库 |
| Git | 最新稳定版 | git --version | 代码管理 |

---

## 4. 配置环境变量

```bash
cp .env.example .env
```

---

## 5. 初始化数据库

```bash
mysql -u root -p your_database < sql/database.sql
```

---

## 6. 启动后端

```bash
cd backend
npm install
npm run dev
```

---

## 7. 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

## 8. 编程工具打开方式

用 Cursor / Trae / VS Code / Windsurf 打开项目根目录，并先阅读：

```text
START_HERE.md
README.md
docs/
sql/database.sql
```
