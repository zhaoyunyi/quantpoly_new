# 能力等价矩阵（用户旅程 × 限界上下文）

## 1. 判定原则

- 判定对象是**功能能力**而非旧接口兼容。
- 每个单元格至少要有 1 条可执行 Given/When/Then 场景。
- `critical=true` 的能力缺失直接阻断 Wave 切换。

## 2. 矩阵

| 用户旅程 | user-auth | user-preferences | strategy-management | backtest-runner | trading-account | market-data | risk-control | signal-execution | monitoring-realtime |
|---|---|---|---|---|---|---|---|---|---|
| 认证登录 | ✅ critical | - | - | - | - | - | - | - | - |
| 用户偏好 | - | ✅ | - | - | - | - | - | - | - |
| 策略管理 | - | - | ✅ critical | - | - | - | - | - | - |
| 回测执行与结果 | - | - | ✅ | ✅ critical | - | ✅ | - | - | ✅ |
| 交易账户与下单 | - | - | - | - | ✅ critical | ✅ | ✅ | ✅ | ✅ |
| 风控告警处置 | - | - | - | - | ✅ | - | ✅ critical | ✅ | ✅ |
| 实时监控 | - | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ critical |

## 3. 输出字段（用于 CLI）

每条能力项输出：

- `id`: 能力标识（如 `auth_login`）
- `passed`: 是否通过
- `critical`: 是否关键能力
- `context`: 所属限界上下文
- `journey`: 所属用户旅程
