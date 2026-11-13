# 工程校验模板

## 1. 本地校验命令

```bash
# 安装依赖
npm install

# 代码格式和静态检查
npm run lint
npm run typecheck

# 测试
npm test

# 构建
npm run build
```

## 2. 后端校验命令

```bash
# 示例，根据技术栈替换
npm run test:unit
npm run test:integration
npm run start:dev
```

## 3. 数据库校验

```bash
mysql -u 用户名 -p 数据库名 < sql/database.sql
```

## 4. CI 最小门禁

- [ ] 安装依赖成功
- [ ] lint / format 通过
- [ ] 类型检查通过
- [ ] 单元测试通过
- [ ] 构建通过
- [ ] 安全扫描无高危问题
