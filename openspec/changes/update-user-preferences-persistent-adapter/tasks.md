## 1. 持久化接入

- [ ] 1.1 实现偏好 sqlite store（含 schema 初始化）
- [ ] 1.2 在组合入口按 storage_backend 注入偏好 store
- [ ] 1.3 保持 version/migrate/deep-merge 语义一致

## 2. API 与 CLI

- [ ] 2.1 现有 preferences API 无破坏升级
- [ ] 2.2 CLI 支持读取/更新/导入导出 JSON

## 3. 测试与验证

- [ ] 3.1 先写失败测试（Red）：更新偏好后重启仍可读取
- [ ] 3.2 验证 level1 对 advanced 字段权限不变
- [ ] 3.3 运行 `openspec validate update-user-preferences-persistent-adapter --strict`
