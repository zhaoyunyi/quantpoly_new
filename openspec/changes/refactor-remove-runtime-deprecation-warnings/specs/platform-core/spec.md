## ADDED Requirements

### Requirement: 默认执行路径不得产生已知弃用告警
系统在默认 CLI/API 执行路径下 MUST 不产生已知可修复的 Python 弃用告警，避免 CI 噪音与升级风险累积。

#### Scenario: 流网关事件时间戳不触发 datetime 弃用告警
- **GIVEN** 用户建立市场流网关连接
- **WHEN** 服务端生成事件时间戳
- **THEN** 不应触发 `datetime.utcnow()` 相关弃用告警

#### Scenario: 偏好 CLI 解析器初始化不触发 argparse FileType 弃用告警
- **GIVEN** 客户端初始化偏好 CLI 解析器
- **WHEN** 构建命令行参数定义
- **THEN** 不应触发 `argparse.FileType` 相关弃用告警
