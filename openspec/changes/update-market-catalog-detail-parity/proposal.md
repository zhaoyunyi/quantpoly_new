## Why

源项目市场接口包含按 symbol 的资产详情语义（`/market/stocks/{symbol}`）。
当前项目已有 `catalog/search/quote/history`，但缺少单资产详情端点，前端需要多次拼装请求。

## What Changes

- 新增市场资产详情端点：按 `symbol` 返回标准化资产读模型（`symbol/name/exchange/assetClass/status`）。
- 目录查询支持可选过滤（`market`、`assetClass`），用于缩小资产范围。
- CLI 增加 `catalog-detail` 命令，`catalog` 支持同名过滤参数，保持 API/CLI 语义一致。

## Impact

- 影响 capability：`market-data`
- 风险：Provider 不同导致资产字段可用性不一致，已统一 `status = active|inactive` 映射并保留字段缺省输出。
