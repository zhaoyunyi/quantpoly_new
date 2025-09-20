## Why

当前交易域已具备订单生命周期能力，但产品层仍缺少“业务指令语义”入口（buy/sell command）。
在“兼容可 break、功能不缺失”的策略下，仍应提供面向用户旅程的一键交易入口，避免前端拼装多步状态机流程。

## What Changes

- 在 `trading-account` 增加业务级 buy/sell 指令入口（可内部复用订单生命周期实现）。
- 明确 buy/sell 与订单/成交/资金流水的一致性关系与错误语义。
- 补齐 CLI 命令与 GWT 测试。

## Impact

- 影响 capability：`trading-account`
- 不要求保留源项目旧路径，但必须保留等价业务能力。
