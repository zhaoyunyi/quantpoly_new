## 1. 领域能力

- [ ] 1.1 在交易应用服务增加 buy/sell command façade
- [ ] 1.2 复用现有订单状态机并保证事务一致性
- [ ] 1.3 明确资金不足/持仓不足/风控拒绝错误码

## 2. API 与 CLI

- [ ] 2.1 提供业务指令入口 API（路径可 break，语义不可缺失）
- [ ] 2.2 补齐 CLI buy/sell 命令，支持 JSON 输入输出

## 3. 测试与验收

- [ ] 3.1 先写失败测试（Red）：买入成功、卖出成功、资金不足、持仓不足
- [ ] 3.2 通过 Given/When/Then 验证订单/成交/流水一致性
- [ ] 3.3 运行 `openspec validate update-trading-command-entry-parity --strict`
