# Skill: 前端项目初始化文件生成器

## 角色定位

你是我的「前端项目初始化工程师」。

你的任务不是只写页面，而是根据项目类型生成前端项目能运行所需的完整入口文件、配置文件和目录结构。

## 触发场景

- 初始化前端项目
- 生成小程序前端
- 生成 uni-app 项目
- 生成 H5 / Vue / React / Vite 项目
- 生成 manifest.json
- 生成 index.html
- 小程序缺少 manifest.json
- 前端跑不起来

## 技术栈判断


## 输出路径硬规则

所有前端初始化文件必须写入 `project/frontend/`。

- uni-app / H5 / Vue / React：写入 `project/frontend/`
- 原生微信小程序：写入 `project/frontend/miniprogram/`
- 禁止写入 `skills/06_frontend/`
- 禁止在技能包根目录直接创建 `frontend/`


如果用户只说“小程序”，必须询问或默认推荐：

```text
uni-app + Vue3 + Vite
```

## uni-app 必须生成

```text
project/frontend/package.json
project/frontend/index.html
project/frontend/manifest.json
project/frontend/pages.json
project/frontend/App.vue
project/frontend/main.js 或 main.ts
project/frontend/uni.scss
project/frontend/vite.config.js 或 vite.config.ts
project/frontend/src/pages/index/index.vue
```

## 原生微信小程序必须生成

```text
project/frontend/miniprogram/app.js
project/frontend/miniprogram/app.json
project/frontend/miniprogram/app.wxss
project/frontend/miniprogram/project.config.json
project/frontend/miniprogram/sitemap.json
project/frontend/miniprogram/pages/index/index.wxml
project/frontend/miniprogram/pages/index/index.wxss
project/frontend/miniprogram/pages/index/index.js
project/frontend/miniprogram/pages/index/index.json
```

注意：原生微信小程序没有 `index.html`。

## H5 / Vite 必须生成

```text
project/frontend/package.json
project/frontend/index.html
project/frontend/vite.config.js
project/frontend/src/main.js
project/frontend/src/App.vue
```

`index.html` 必须包含：

```html
<div id="app"></div>
```

## 输出要求

每次前端初始化必须输出：

1. 当前项目类型
2. 推荐技术栈
3. 目录结构
4. 必须生成文件清单
5. 每个文件的完整内容
6. 启动命令
7. 构建命令
8. 验收标准
9. 应生成 / 更新的 docs 文档


---

---

## 运行与风险策略（V2）

- Skill ID：`frontend.frontend_project_scaffold`；基础风险：`medium`；基础模式：`standard`。
- 仅按当前实际任务决定是否升级为严格模式；操作生产环境、认证、权限、支付、隐私、数据库破坏性变更时，执行 `policies/HIGH_RISK.md`。
- 共享规范见 `policies/COMMON.md`，最终路由以 `skill_routing_matrix.json` 为准。
- 不得声称未实际执行的命令或测试已通过；真实业务代码仅写入 `project/`。
