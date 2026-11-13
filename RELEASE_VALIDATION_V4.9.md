# V4.9 本地发布验证记录

日期：2026-11-13

## 真正运行的检查

| 检查 | 状态 |
|---|---|
| Python 既有和新增测试，四组分独立进程 | Core 106、Analysis 143、Platform 36、Collaboration 120；共 **405/405** 通过 |
| V4.9 供应链专项单元测试 | **18/18** 通过，包括签名/公钥验签与损坏文件拦截 |
| 固定路由基准 | 28/28 通过 |
| Skill 目录与路由引用审计 | 144 个技能，0 个错误 |
| Smoke 工程验收 | 4/4 通过 |
| Todo API 单独运行 | 11/11 通过（从 examples/runnable-todo 执行） |
| Node.js 项目样例 | 1/1 通过 |
| TypeScript 类型检查 | 本地已安装 TypeScript，`tsc --noEmit` 通过 |
| GitHub Actions 引用静态审计 | 5 类固定 SHA、18 处引用，一致性检查通过 |
| 依赖锁元数据校验 | TypeScript 5.9.3，SRI 与 package-lock 结构检查通过 |

历史脚本曾启动全量串行测试，但受工具执行时间限制中断，该尝试**不算执行通过**。以上 405 项由四个完整执行并分别返回成功的分组组成。

## 发布过程验证

V4.9 ZIP 由固定时间戳和文件排序的打包器构建；每个归档成员以 SHA-256 和清单重新核验，附带整体 `.sha256`、未签名的本地发布元数据及 CycloneDX 结构依赖清单。从最终 ZIP 重新解压验证版本信息与核心文件。

## 尚未验证

- 未取得真实 GitHub Actions Linux/Windows/macOS 三平台运行回执，也未通过 GitHub 身份认证的 attestation。
- 环境无法联网，未从 npm Registry 真正执行 `npm ci` 下载；TypeScript 5.9.3 安装在本机，已有 TypeScript 类型检查通过。
- 未提供真实发布者私钥，因此**交付 ZIP 未正式签名**；测试中临时生成的密钥只验证签名/验签程序功能。
- 固定 Actions SHA 降低标签漂移风险，但不等于已经审计上游 Action 实现或 GitHub runners。

详细文档：`docs/ENGINEERING_V4.9.md`。
