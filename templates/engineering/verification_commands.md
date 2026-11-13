# 验证命令模板

开发类、调试类、部署类、安全类 Skill 必须输出“本次应运行的验证命令”。无法运行时必须明确说明未实际验证。

## Node.js / TypeScript

```bash
npm install
npm run lint
npm run typecheck
npm run test
npm run build
```

## Vue / Vite / uni-app

```bash
npm run dev
npm run build
npm run preview
```

## Python

```bash
python -m pytest
ruff check .
mypy .
```

## Docker / Docker Compose

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

## 数据库

```bash
mysql < sql/database.sql
# 测试库执行迁移 SQL
# 测试库执行回滚 SQL
# 执行验证 SQL
```

## API

```bash
# 使用 curl / Postman / Apifox / OpenAPI 工具校验
# 检查 2xx / 4xx / 5xx / 权限失败 / 参数错误返回结构
```

## 安全

```text
- 权限 / 越权测试
- SQL 注入输入测试
- XSS 输入测试
- 文件上传类型/大小/权限测试
- 日志敏感信息检查
- 环境变量/密钥泄露检查
```

## 输出格式要求

每个开发类 Skill 最后必须输出：

| 验证项 | 命令/方法 | 预期结果 | 失败时进入的 Skill |
|---|---|---|---|
| Lint | npm run lint | 0 error | code_quality.code_review |
| 单元测试 | npm run test | 全部通过 | integration_debugging.systematic_debugging |
| 构建 | npm run build | 构建成功 | integration_debugging.systematic_debugging |
