## ADDED Requirements

### Requirement: 同步任务结果必须支持边界一致性校验
数据同步任务完成后 MUST 提供边界一致性校验入口，确认数据归属与 ACL 访问规则未被破坏。

#### Scenario: 同步后触发边界校验
- **GIVEN** 一次跨来源数据同步任务已完成
- **WHEN** 执行边界一致性校验
- **THEN** 输出一致性报告（missing/extra/mismatch）
- **AND** 发现违规时返回可追踪错误结果
