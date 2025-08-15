## 1. 读模型扩展

- [x] 1.1 增加账户风险指标读模型（risk-metrics）
- [x] 1.2 增加权益曲线读模型（equity-curve）
- [x] 1.3 增加仓位分析读模型（position-analysis）
- [x] 1.4 增加用户级账户聚合统计视图

## 2. 运维能力补齐

- [x] 2.1 增加待处理交易查询接口（受角色限制）
- [x] 2.2 增加价格刷新入口（受治理授权与审计）
- [x] 2.3 补齐 API/CLI 输出的稳定错误码与响应契约

## 3. 一致性与治理

- [x] 3.1 强制账户所有权校验（含聚合统计）
- [x] 3.2 管理员操作接入 `admin-governance`
- [x] 3.3 指标口径与 `risk-control` 评估语义对齐

## 4. 测试与校验

- [x] 4.1 按 TDD 增加读模型/API/CLI 测试
- [x] 4.2 覆盖越权读取、批量刷新冲突、审计脱敏场景
- [x] 4.3 运行 `openspec validate update-trading-analytics-ops-parity --strict`
