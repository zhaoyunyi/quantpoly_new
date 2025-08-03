# data-topology-boundary Specification

## Purpose
TBD - created by archiving change add-data-topology-boundary-migration. Update Purpose after archive.
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

