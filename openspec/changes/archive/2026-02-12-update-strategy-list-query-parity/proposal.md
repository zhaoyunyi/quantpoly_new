## Why

源项目策略列表支持分页、状态筛选与关键词搜索；当前后端 `GET /strategies` 仅返回当前用户全量策略。
在策略数量增长场景下，缺少查询分层会导致前端性能与交互退化。

## What Changes

- 为策略列表增加查询参数：`status`、`search`、`page`、`pageSize`。
- 输出结构升级为分页读模型：`items/total/page/pageSize`。
- CLI `list` 子命令支持相同过滤参数并输出分页元信息。
- 保持用户隔离语义不变（所有查询仍受 `current_user.id` 约束）。

## Impact

- 影响 capability：`strategy-management`
- 风险：列表返回结构从数组变为分页对象，前端调用方需同步适配（break update）

## Break Update 迁移说明

- API `GET /strategies` 响应从 `data: Strategy[]` 变更为：
  - `data.items`
  - `data.total`
  - `data.page`
  - `data.pageSize`
- API 新增查询参数：`status`、`search`、`page`、`pageSize`
- CLI `list` 输出从数组变更为分页对象；新增参数：`--status --search --page --page-size`
