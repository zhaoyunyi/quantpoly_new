## 1. 领域与服务补齐

- [x] 1.1 增加策略参数校验服务（模板约束 + 错误码）
- [x] 1.2 增加信号生成与处理应用服务（含幂等保护）
- [x] 1.3 增加执行记录读模型（详情/运行中/趋势）

## 2. API 与 CLI 补齐

- [x] 2.1 新增参数校验与信号生成接口
- [x] 2.2 新增执行详情、执行取消、运行中查询接口
- [x] 2.3 新增执行统计/趋势接口
- [x] 2.4 提供对应 CLI 命令与 JSON 输出

## 3. 一致性与权限

- [x] 3.1 全部执行接口强制 `strategyId/accountId` 所有权校验
- [x] 3.2 统一错误 envelope（校验失败/冲突/越权）
- [x] 3.3 高风险维护动作接入 `admin-governance`

## 4. 测试与校验

- [x] 4.1 按 TDD 增加服务/API/CLI 覆盖
- [x] 4.2 覆盖并发执行、重复提交、越权访问用例
- [x] 4.3 运行 `openspec validate update-strategy-execution-control-parity --strict`
