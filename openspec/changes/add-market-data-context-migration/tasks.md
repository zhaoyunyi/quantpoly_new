## 1. 领域与 Provider 适配

- [ ] 1.1 新建 `libs/market_data` 并定义统一行情查询接口
- [ ] 1.2 抽象 Alpaca Provider，封装超时、重试、错误映射
- [ ] 1.3 为常见查询提供 CLI（quote/history/search）

## 2. API 与缓存

- [ ] 2.1 增加市场数据 API 路由并统一 envelope
- [ ] 2.2 增加短时缓存与限流策略
- [ ] 2.3 补充缓存命中与降级测试

## 3. 验证

- [ ] 3.1 覆盖 provider 失败降级与错误码规范
- [ ] 3.2 运行 `pytest -q` 与 `openspec validate add-market-data-context-migration --strict`

