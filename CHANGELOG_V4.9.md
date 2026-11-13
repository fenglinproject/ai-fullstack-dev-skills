# V4.9 更新记录

发布日期：2026-11-13

- 将 5 种 GitHub Actions（共 18 处引用）固定为审计过的 40 位提交 SHA，并在 checkout 禁用持久化凭据。
- 添加 `package.json`、`package-lock.json`，固定 TypeScript 5.9.3 及 npm SRI；工作流使用 `npm ci --ignore-scripts`。
- 添加 `ci/actions_pins.json`、`tools/supply_chain_v49.py`，提供固定引用、锁元数据和 CI 安装策略的本地审计。
- 添加 `tools/package_release_v49.py`，保留 V4.8 打包接口，同时新增 V4.9 可复验的 ZIP 与 SHA-256 侧车文件。
- 提供未签名的 in-toto 结构发布元数据、CycloneDX 结构的最小依赖清单，以及明确授权的 OpenSSL RSA/ECDSA 签名/验签。
- `fullstack.py` 新增 `supply-chain` 与 `release-package-v49`；旧 CLI 入口仍然保留。
- 新增 `tests/test_v49.py` 的 18 项专项测试及独立进程发布矩阵入口。

注意：未经可信密钥签名的哈希与发布元数据不等于软件来源认证；未实测 GitHub 三平台在线 CI 与联网 npm 安装。
