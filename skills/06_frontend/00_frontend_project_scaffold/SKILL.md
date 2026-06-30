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

如果用户只说“小程序”，必须询问或默认推荐：

```text
uni-app + Vue3 + Vite
```

## uni-app 必须生成

```text
frontend/package.json
frontend/index.html
frontend/manifest.json
frontend/pages.json
frontend/App.vue
frontend/main.js 或 main.ts
frontend/uni.scss
frontend/vite.config.js 或 vite.config.ts
frontend/src/pages/index/index.vue
```

## 原生微信小程序必须生成

```text
miniprogram/app.js
miniprogram/app.json
miniprogram/app.wxss
miniprogram/project.config.json
miniprogram/sitemap.json
miniprogram/pages/index/index.wxml
miniprogram/pages/index/index.wxss
miniprogram/pages/index/index.js
miniprogram/pages/index/index.json
```

注意：原生微信小程序没有 `index.html`。

## H5 / Vite 必须生成

```text
frontend/package.json
frontend/index.html
frontend/vite.config.js
frontend/src/main.js
frontend/src/App.vue
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
