## 1. 测试工具链

- [ ] 1.1 引入 Vitest + React Testing Library（或等价）
- [ ] 1.2 增加脚本：
  - [ ] `npm run test`（unit）
  - [ ] `npm run test:e2e`（playwright）
  - [ ] `npm run test:contract`（contract）
- [ ] 1.3 建立测试目录结构：`apps/frontend_web/tests/unit`、`apps/frontend_web/tests/e2e`

## 2. Contract tests（对齐后端契约）

- [ ] 2.1 定义最小 contract：success/error envelope、分页结构
- [ ] 2.2 覆盖关键接口：
  - [ ] `GET /users/me`
  - [ ] `GET /strategies`
  - [ ] `GET /backtests`
  - [ ] `GET /trading/accounts`
  - [ ] `GET /monitor/summary`

## 3. E2E 主链路（可并行）

- [ ] 3.1 登录 -> Dashboard
- [ ] 3.2 策略创建（from-template）-> 列表可见
- [ ] 3.3 提交回测 -> 状态展示 -> 查看结果（未就绪分支）
- [ ] 3.4 交易账户创建 -> 下单（buy/sell）-> 订单列表刷新
- [ ] 3.5 Monitor：连接 WS -> 展示 signals/alerts（可用 mock server）

## 4. 回归验证

- [ ] 4.1 `cd apps/frontend_web && npm run build`
- [ ] 4.2 `pytest -q`

