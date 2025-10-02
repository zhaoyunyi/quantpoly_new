## 1. 读模型与查询

- [ ] 1.1 定义资产详情读模型（symbol/name/exchange/assetClass/status）
- [ ] 1.2 定义目录过滤参数（market/assetClass）

## 2. API 与 CLI

- [ ] 2.1 新增资产详情 API
- [ ] 2.2 catalog API 支持过滤参数
- [ ] 2.3 CLI 增加资产详情与过滤查询能力

## 3. 测试与验证

- [ ] 3.1 Red：详情查询、过滤查询、不存在 symbol
- [ ] 3.2 Green：实现与回归
- [ ] 3.3 运行 `openspec validate update-market-catalog-detail-parity --strict`
