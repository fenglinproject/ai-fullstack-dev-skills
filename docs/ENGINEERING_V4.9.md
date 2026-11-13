# V4.9 工程指南：固定依赖、发布元数据和可验证签名

## 安全模型和已验证范围

- 所有 `.github/workflows/test.yml` 第三方 Action 引用固定到经过公开来源查阅的完整 40 位提交 SHA；`ci/actions_pins.json` 是本仓库审核基线。固定 SHA 仅能防止标签移动，不能保证对应第三方代码无漏洞。
- CI 使用 `npm ci --ignore-scripts` 和 `package-lock.json` 固定 TypeScript 5.9.3（含 npm SRI）。Python 运行核心仅用标准库。**本环境无法联网，因此尚未执行真实 registry 下载的 `npm ci`**，但对锁元数据进行了静态一致性检查。CI 会在实际运行时由 npm 核验下载包完整性。
- 发布包在 `tools/package_release_v49.py` 中采用 SHA-256 逐文件校验，外部 `.sha256` 校验文件可检测损坏，但不能证明来源。
- `provenance.json` 是可核对的 **未签名本地发布元数据**，不是 SLSA、GitHub 原生 attestation 或可信第三方声明。`sourceCommit` 和 `githubRunId` 只是声明值，不能仅凭它们证明 GitHub 的身份。
- 只有使用你自己持有的可信 PEM 私钥生成 `.sig`，并从独立可信渠道取得公钥完成验证，才能为发布提供具有密钥信任前提的签名校验。工具包不包含真实私钥或正式签名。

## 1. 依赖和 Actions 审计

```bash
python fullstack.py supply-chain audit
# 或 python tools/supply_chain_v49.py audit
```

审计拒绝标签形式的可变 Action、未列入允许清单的 Action、损坏的 TypeScript SRI 元数据、未通过 `npm ci` 安装及新增的 package.json 生命周期脚本。审核仍需进一步核对上游 Action 版本、许可证、已知漏洞和签名者身份。

## 2. CI 中安装依赖

```bash
npm ci --ignore-scripts --no-audit --no-fund
./node_modules/.bin/tsc --project benchmarks/projects/ts-workspace/tsconfig.json --noEmit
```

本工具包不依赖任何额外的 Python 第三方运行时包。不要手动编辑锁文件；后续更新 TypeScript 应在可信联网环境中运行 npm CLI 并核对升级差异，再提交新的完整性哈希。

## 3. 制作与检查发布包

```bash
mkdir -p dist
python fullstack.py release-package-v49 --output dist/ai-fullstack-dev-skills-v4.9.zip --execute
python fullstack.py release-package-v49 --verify dist/ai-fullstack-dev-skills-v4.9.zip
python fullstack.py supply-chain provenance --archive dist/ai-fullstack-dev-skills-v4.9.zip --output dist/ai-fullstack-dev-skills-v4.9.provenance.json
python fullstack.py supply-chain verify-provenance --archive dist/ai-fullstack-dev-skills-v4.9.zip --statement dist/ai-fullstack-dev-skills-v4.9.provenance.json
python fullstack.py supply-chain sbom --output dist/ai-fullstack-dev-skills-v4.9.sbom.json
```

`release-package-v49` 拒绝覆盖已存在的 ZIP 或校验文件。生成 `provenance` 时可附加 `--commit <40位SHA> --run-id <GitHub数字ID>`，但这两个字段依然是**未经平台验证的声明**。SBOM 只说明锁文件中的 TypeScript 包，不是对用户实际设备的完整依赖扫描。

## 4. 已有签名密钥时由授权人员生成签名

仅支持 OpenSSL `dgst -sha256` 可签名的 RSA/ECDSA PEM 私钥。**不要把私钥放在 Git 仓库、ZIP 或对话里。**

```bash
python fullstack.py supply-chain sign --archive dist/ai-fullstack-dev-skills-v4.9.zip --private-key /secure/path/release-private.pem --output dist/ai-fullstack-dev-skills-v4.9.sig --approve
python fullstack.py supply-chain verify-signature --archive dist/ai-fullstack-dev-skills-v4.9.zip --public-key /trusted/path/release-public.pem --signature dist/ai-fullstack-dev-skills-v4.9.sig
```

CLI 只检验签名是否和给定公钥相符；**无法核对该公钥是否属于正确发布方**。当前交付的 ZIP 未使用任何真实用户私钥签名。

## 5. 跨平台 GitHub Actions

旧 V4.8 的 8 份证据合同保持兼容；Linux 全量回归与 Windows/macOS 锁测试仍由 `.github/workflows/test.yml` 编排。新版本打包只有在 `aggregate` job 成功之后才触发。

已在本地完成的验证，不应替代真实 GitHub-hosted runner 的三平台回执。实际仓库应检查每次 Actions run 的具体 SHA、所有工作是否成功，以及下载的发布候选产物。

## 6. 常见限制

- SHA 固定不能替代第三方代码审计；`ubuntu-latest` 等 GitHub runner 标签仍由 GitHub 托管与更新。
- 目前没有 OIDC/Sigstore 身份绑定的原生 GitHub artifact attestation；需要另行配置受信任的发布身份和平台验证。
- Windows/macOS 真实 GitHub Actions，以及联网运行的 `npm ci`，均不属于本次本地验证。
- 本地 OpenSSL 临时测试密钥仅用于单元测试；它绝不是正式的发布签名凭据。
