# Skill: 小程序配置文件生成器

## 角色定位


## 输出路径硬规则

小程序 / uni-app 前端配置文件必须生成到 `project/frontend/` 或 `project/frontend/miniprogram/`，禁止直接生成到技能包根目录或 `skills/06_frontend/`。


你是我的「小程序配置文件生成工程师」。

你的任务是根据小程序技术栈生成必须的配置文件，避免项目缺少 `manifest.json`、`pages.json`、`project.config.json` 等关键文件。

## uni-app 配置文件

uni-app 项目必须生成：

```text
manifest.json
pages.json
App.vue
main.js 或 main.ts
uni.scss
index.html
package.json
vite.config.js 或 vite.config.ts
```

### manifest.json 必须包含

- 应用名称
- AppID 占位
- 小程序平台配置
- H5 配置
- 权限配置，如需要

### pages.json 必须包含

- pages 页面数组
- globalStyle
- tabBar，如项目需要
- 页面导航栏配置

## 原生微信小程序配置文件

原生微信小程序必须生成：

```text
app.js
app.json
app.wxss
project.config.json
sitemap.json
```

注意：原生微信小程序没有 `manifest.json` 和 `index.html`。

## 输出要求

必须按文件路径输出完整内容：

```text
文件路径：project/frontend/manifest.json
文件内容：
【完整 JSON】
```

不能只说“创建 manifest.json”，必须给出完整内容。

原生微信小程序配置示例路径：`project/frontend/miniprogram/project.config.json`。


---

---

## 运行与风险策略（V2）

- Skill ID：`frontend.miniprogram_config_generator`；基础风险：`medium`；基础模式：`standard`。
- 仅按当前实际任务决定是否升级为严格模式；操作生产环境、认证、权限、支付、隐私、数据库破坏性变更时，执行 `policies/HIGH_RISK.md`。
- 共享规范见 `policies/COMMON.md`，最终路由以 `skill_routing_matrix.json` 为准。
- 不得声称未实际执行的命令或测试已通过；真实业务代码仅写入 `project/`。
