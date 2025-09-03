## 1. 需求与合同（Spec）

- [x] 1.1 增加/修改 `market-data` 指标套件需求 delta（含场景）
- [x] 1.2 增加 API 合同测试：RSI/MACD/BOLL 成功路径
- [x] 1.3 增加 API 合同测试：`unsupported` / `insufficient_data` 语义
- [x] 1.4 增加 CLI 合同测试：JSON 输入输出结构稳定

## 2. 指标实现（Library-First）

- [x] 2.1 实现 `EMA` 指标计算
- [x] 2.2 实现 `RSI` 指标计算
- [x] 2.3 实现 `MACD` 指标计算
- [x] 2.4 实现 `Bollinger Bands` 指标计算
- [x] 2.5 对齐输出结构与错误码

## 3. 验证

- [x] 3.1 运行相关 pytest（只跑新增覆盖范围）
- [x] 3.2 运行 `openspec validate update-market-data-indicator-suite-parity --type change --strict`
