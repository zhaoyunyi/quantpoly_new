# frontend-strategy-management Specification

## Purpose
TBD - created by archiving change add-frontend-strategy-management-pages. Update Purpose after archive.
## Requirements
### Requirement: Frontend SHALL provide strategy list management at /strategies

前端 SHALL 在 `/strategies` 提供策略列表管理能力（搜索、筛选、分页与基础操作）。

#### Scenario: List strategies with pagination
- **GIVEN** 用户已登录
- **WHEN** 打开 `/strategies`
- **THEN** 前端调用 `GET /strategies?page=1&pageSize=20`
- **AND** 渲染策略列表与分页控件

#### Scenario: Delete strategy shows conflict reason when in use
- **GIVEN** 用户尝试删除策略
- **WHEN** 后端返回 409 `STRATEGY_IN_USE`
- **THEN** 前端展示不可删除原因并保持列表一致性

### Requirement: Frontend SHALL provide strategy detail page at /strategies/$id

前端 SHALL 在 `/strategies/$id` 提供策略详情与编辑能力，并展示关联回测。

#### Scenario: View strategy detail and related backtests
- **GIVEN** 用户已登录且拥有该策略
- **WHEN** 打开 `/strategies/$id`
- **THEN** 前端调用 `GET /strategies/{id}`
- **AND** 前端调用 `GET /strategies/{id}/backtests`
- **AND** 展示策略信息与回测列表

