# V4.4 工程指南：已有 Git 仓库接入、并行冲突和离线 CI 核查

## 升级目标

V4.4 在 V4.3 的本地 Git 提交与验收证据基础上，加入针对**用户已存在的、可信的本地 Git 项目**的只读接入流程。默认不修改源码、不联网、不运行项目测试、不自动创建 Git 分支或提交。

主要入口为 `python fullstack.py repo-readiness`、`repo-conflicts`、`repo-trial`，也可以单独运行 `tools/repo_readiness_v44.py` / `tools/repo_trial_v44.py`。保留全部 144 个技能和旧版工具。

## 1. 接入已有仓库：先只读核对

以下命令必须指向**已存在并有 HEAD 提交的 Git 工作区根目录**：

```bash
python fullstack.py repo-readiness --project /absolute/path/to/trusted-repo

# 固定基线，工作区必须干净；这仍然只是本地预检
python fullstack.py repo-readiness --project /absolute/path/to/trusted-repo \
  --expected-head FULL_GIT_COMMIT_SHA --require-clean
```

输出会提供 Git HEAD、分支、工作区脏记录数、静态技术栈标记、`.ai` 初始化状态，以及审计发现的警告/阻断项。**不会读取业务源码正文或执行脚本**。对于尚未初始化 `.ai` 的仓库，返回 `needs_initialization`；只有用户审查后显式运行 `python fullstack.py project init --project ...` 才会创建本地状态。工具不会代替你执行这一步。

`repo-readiness` 的返回状态分别为 `reviewable`（无当前发现的阻断项）、`needs_initialization`（缺少本地状态）、`blocked`（发现问题）；**`reviewable` 不表示生产安全、代码正确或已完成 CI 信任验证**。

> Git 自身的配置、属性过滤器等在特定操作下仍可能调用系统工具。建议仅对自己信任的本地 Git 仓库运行这些检查。项目可包含私有文件名，因此请自行保护终端输出和 JSON 报告。

## 2. 并行任务重叠检测（只读、非锁）

```bash
python fullstack.py repo-conflicts --project /absolute/path/to/trusted-repo \
  --candidate src/payment.py --candidate tests/test_payment.py
```

工具会有界扫描 `.ai/changes/*/manifest.json` 的 `prepared`、`applied` 状态，识别当前未结束的变更以及不同变更之间的**文件路径冲突**。已提交的 `committed` 历史记录不会长期占用文件。

候选路径必须是相对文件路径，拒绝路径穿越和软链接；每次扫描有记录数上限。遇到损坏、过量记录或中断状态会失败关闭或报告阻断。

**注意：这只是预检快照，不是跨进程保留锁，也不自动拒绝全部并行修改、推断语义级冲突或完成自动合并。** 用户应在做实际文件修改之前再次审查，并使用原有审批、Git 分支和恢复机制。

## 3. 可选的离线 CI JSON 核查

从你信任的 CI 系统自行导出/制作如下简化结构（文件存放于自行指定的本地位置，工具不联网）：

```json
{
  "schema_version": 1,
  "provider": "github-actions",
  "run_id": "123456",
  "commit": "FULL_40_OR_64_CHARACTER_COMMIT_SHA",
  "checks": [
    {"name": "lint", "status": "completed", "conclusion": "success"},
    {"name": "tests", "status": "completed", "conclusion": "success"}
  ]
}
```

```bash
python fullstack.py repo-readiness --project /absolute/path/to/trusted-repo \
  --require-clean --require-ci --ci-receipt /path/to/ci-receipt.json \
  --required-check lint --required-check tests
```

工具验证 JSON 结构、必要检查是否成功、提交 SHA 是否与本地 HEAD 相同，计算文件 SHA-256 供本地复核，但**不会验证 JSON 文件的来源、签名、CI 平台身份或远端仓库归属**。任意本地用户都可能伪造内容，因此这只是一条 `unsigned-local-JSON` **不可信线索**，绝不能替代 V4.3 的受控测试证据、真实 CI 系统审查或生产权限审批。不会自动解锁 Git commit / PR / 发布。

CI 报告最大 128 KiB，拒绝软链接、重复检查名称和无效状态；默认不把报告正文转送给模型或网页。CI 检查仅在用户显式提供时启用。

## 4. 本地可靠性采样和演示

```bash
# 在自己已有的可信 Git 仓库上执行只读短时间采样，默认 5 次
python fullstack.py repo-trial --project /absolute/path/to/trusted-repo \
  --samples 5 --require-clean

# 使用由工具自己创建的独立临时 Git 项目测试接入流程，不执行项目测试
python examples/v44-repo-demo/run_demo.py

# 明确同意执行随包可信示例的测试：会生成 2 个真实本地 Git 提交
python examples/v44-repo-demo/run_demo.py --execute-tests
```

采样记录每次审计的状态、HEAD 和读取延迟中位数，不后台持续运行、不覆盖文件，也不能证明数周稳定性。演示创建独立临时目录，本地完成后自动清理，绝不会操作你的业务仓库，也没有远程推送。

## 5. 推荐接入步骤

先备份仓库并确认可信 → 使用 `repo-readiness` 只读检查 → 发现问题先人工审查 → 初始化独立 `.ai` 状态（仅在接受写入后） → 用 `repo-conflicts` 检查候选变更 → 在 `ai/*` 分支上沿用 V3 的人工审批和测试流程 → 提交前依据受控测试报告核查 → 另行在受信任的 CI 平台核对构建成功。

## 6. 工程边界

- 没有接入用户的私人真实仓库、线上 GitHub/GitLab 项目或生产环境。
- 没有运行未知项目的测试、构建或第三方部署脚本；本轮真实提交来自可信临时样例。
- 没有自动拉取仓库、推送 Git、创建远程 PR 或自动合并。
- 离线 CI JSON 不是可信签名，也不用于代码提交授权。
- 路径级冲突检测只发现部分并行修改风险，不是原子锁或语义级合并器。
- `repo-trial` 的短时间重复采样不是长期压力测试；需要在实际仓库上独立积累长期数据。

主要测试：`python -m unittest tests.test_v44 -q`。更多记录参见 `CHANGELOG_V4.4.md` 和 `RELEASE_VALIDATION_V4.4.md`。
