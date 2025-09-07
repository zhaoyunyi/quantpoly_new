## 1. 需求与合同（Spec）

- [ ] 1.1 增加风险规则统计与告警快捷查询需求 delta
- [ ] 1.2 增加信号手动过期与账户统计需求 delta
- [ ] 1.3 增加 API/CLI 合同测试（含越权场景）

## 2. Library-First 实现

- [ ] 2.1 扩展 `RiskControlService`（rule_stats/recent_alerts/unresolved_alerts）
- [ ] 2.2 扩展 `SignalExecutionService`（expire_signal/account_statistics）
- [ ] 2.3 扩展 CLI 命令

## 3. API

- [ ] 3.1 增加 `GET /risk/rules/statistics`
- [ ] 3.2 增加 `GET /risk/alerts/recent`
- [ ] 3.3 增加 `GET /risk/alerts/unresolved`
- [ ] 3.4 增加 `POST /signals/{signalId}/expire`
- [ ] 3.5 增加 `GET /signals/statistics/{accountId}`

## 4. 验证

- [ ] 4.1 运行 `pytest -q libs/risk_control/tests libs/signal_execution/tests`
- [ ] 4.2 运行 `openspec validate update-risk-signal-query-parity --type change --strict`
