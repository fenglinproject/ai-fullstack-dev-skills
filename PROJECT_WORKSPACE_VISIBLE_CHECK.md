# project 工作区可见性检查

本修正版已把真实项目工作区放到压缩包第一层的 `project/` 目录中。

打开压缩包后应能直接看到：

```text
project/
├── backend/README.md
├── frontend/README.md
├── docs/README.md
├── sql/README.md
├── tests/README.md
├── scripts/README.md
└── README.md
```

说明：

- `project/backend/` 是后端真实代码区。
- `project/frontend/` 是前端真实代码区。
- `skills/05_backend/` 和 `skills/06_frontend/` 只是技能说明，不放真实代码。
- 本版每个 project 子目录都加入了可见的 `README.md`，避免因为 `.gitkeep` 是隐藏文件而看起来像空目录。
