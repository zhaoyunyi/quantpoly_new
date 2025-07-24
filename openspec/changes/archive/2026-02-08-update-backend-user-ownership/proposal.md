# 提案：update-backend-user-ownership

## Why（为什么要做）

旧后端的多个业务模型（回测、交易账户等）通过 `user_id: str` 逻辑关联用户，但缺少一致的约束与防越权机制：

- 有的路由使用 `CurrentUser`，有的在 service/repo 层缺少所有权检查
- `CurrentUser` 类型不一致时更容易引发越权与 500

当用户系统迁移到后端后，必须统一“资源所有权（ownership）”规则，并在所有路由中一致执行。

## What Changes（做什么）

- 新增/修改 `backend-user-ownership` capability：
  - 统一 `userId` 的通用语义与跨 bounded context 的使用方式
  - 规定：所有受保护资源必须按 `current_user.id` 过滤或校验
  - 规定：服务层/仓库层的所有对外方法必须显式接收 `user_id`（避免隐式全表查询）

## Impact（影响）

- 防止越权访问（读/写）
- 让策略/回测/交易/风控等模块可并行迁移且不破坏安全边界

