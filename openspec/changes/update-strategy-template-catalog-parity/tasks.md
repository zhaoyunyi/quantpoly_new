## 1. 需求与合同（Spec）

- [ ] 1.1 增加 `strategy-management` 模板目录需求 delta（含场景）
- [ ] 1.2 增加模板列表/参数校验的 API 合同测试（先红）
- [ ] 1.3 增加 CLI 合同测试：模板列表与从模板创建（先红）

## 2. 模板目录实现

- [ ] 2.1 扩展 `_TEMPLATE_CATALOG` 覆盖核心策略模板
- [ ] 2.2 统一参数命名与默认值策略（避免前后端漂移）
- [ ] 2.3 强化 `_validate_parameters`：类型/范围/互斥关系校验
- [ ] 2.4 对齐错误码与错误消息（用于前端提示）

## 3. 验证

- [ ] 3.1 运行相关 pytest
- [ ] 3.2 运行 `openspec validate update-strategy-template-catalog-parity --type change --strict`
