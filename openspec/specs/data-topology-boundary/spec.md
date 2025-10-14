# data-topology-boundary Specification

## Purpose
定义并强制各 bounded context 的数据归属与存储边界：避免跨上下文直接读写他人存储，通过防腐层/开放主机服务进行交互，为迁移与持久化适配提供一致约束。
## Requirements
### Requirement: 数据模型必须归属单一存储边界
每个领域模型 MUST 明确归属单一存储边界（用户域库或业务域库），并禁止运行时隐式跨库路由。

#### Scenario: 模型归属校验失败阻断启动
- **GIVEN** 系统中存在未声明归属或重复归属的模型
- **WHEN** 启动边界校验
- **THEN** 校验失败并阻断服务启动
- **AND** 输出可定位的模型清单

### Requirement: 跨库访问必须通过反腐层接口
跨库读写 MUST 通过显式 ACL/Anti-Corruption Layer 完成，禁止在 repository 层直接跨库 join 或跨库事务。

#### Scenario: repository 直接跨库访问被检测
- **GIVEN** 某 repository 直接引用另一存储边界连接
- **WHEN** 运行边界扫描
- **THEN** 返回违规结果
- **AND** CI 校验失败

### Requirement: 同步任务结果必须支持边界一致性校验
数据同步任务完成后 MUST 提供边界一致性校验入口，确认数据归属与 ACL 访问规则未被破坏。

#### Scenario: 同步后触发边界校验
- **GIVEN** 一次跨来源数据同步任务已完成
- **WHEN** 执行边界一致性校验
- **THEN** 输出一致性报告（missing/extra/mismatch）
- **AND** 发现违规时返回可追踪错误结果

