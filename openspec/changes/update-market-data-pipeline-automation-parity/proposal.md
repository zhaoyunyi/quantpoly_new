## Why

当前市场数据域主要覆盖查询接口，但源项目中的数据同步与技术指标计算任务尚未迁移。
这会导致策略研究与回测依赖的数据管道能力不足，难以形成稳定的数据生产闭环。

## What Changes

- 增加市场数据同步任务与技术指标计算任务能力。
- 补齐同步任务的状态追踪与失败重试语义。
- 增加同步结果与数据边界一致性校验衔接。

## Impact

- Affected specs:
  - `market-data`
  - `data-topology-boundary`
- Affected code:
  - `libs/market_data/*`
  - `libs/job_orchestration/*`
  - `libs/data_topology_boundary/*`
