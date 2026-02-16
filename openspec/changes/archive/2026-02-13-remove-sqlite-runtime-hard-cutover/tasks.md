## 1. 组合入口硬切换

- [x] 1.1 将 `storage_backend` 规范改为 `postgres|memory`
- [x] 1.2 backend_app settings/CLI/app/router 全链路替换 sqlite 参数为 postgres DSN
- [x] 1.3 删除 backend_app 的 sqlite 装配分支并接入 postgres 分支

## 2. 持久化适配器接入

- [x] 2.1 迁入 wave0 可复用 Postgres 适配器（strategy/backtest/job/trading）
- [x] 2.2 补齐组合入口所需的 Postgres 持久化组件（含 user/session/result 等）
- [x] 2.3 确保功能不缺失：风险/信号/偏好能力在 postgres 路径可用

## 3. 测试与规范

- [x] 3.1 先写失败测试（storage/CLI）再改实现（TDD）
- [x] 3.2 运行受影响测试集并修复回归
- [x] 3.3 执行 `openspec validate remove-sqlite-runtime-hard-cutover --strict`
