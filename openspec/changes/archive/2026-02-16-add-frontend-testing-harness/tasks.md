## 1. 测试工具链

- [x] 1.1 引入 Vitest + React Testing Library（或等价）
- [x] 1.2 增加脚本：
  - [x] `npm run test`（unit）
  - [x] `npm run test:e2e`（playwright）
  - [x] `npm run test:contract`（contract）
- [x] 1.3 建立测试目录结构：`apps/frontend_web/tests/{app,pages,api-client,ui-design-system,ui-app-shell,contract}`、`apps/frontend_web/tests/e2e`

## 2. Contract tests（对齐后端契约）

- [x] 2.1 定义最小 contract：success/error envelope、分页结构
- [x] 2.2 覆盖关键接口：
  - [x] `GET /users/me`
  - [x] `GET /strategies`
  - [x] `GET /backtests`
  - [x] `GET /trading/accounts`
  - [x] `GET /monitor/summary`

## 3. E2E 主链路（可并行）

- [x] 3.1 登录 -> Dashboard
- [x] 3.2 策略创建（from-template）-> 列表可见
- [x] 3.3 提交回测 -> 状态展示 -> 查看结果（未就绪分支）
- [x] 3.4 交易账户创建 -> 下单（buy/sell）-> 订单列表刷新
- [x] 3.5 Monitor：连接真实 WS -> 展示 signals/alerts；新增 signal 后列表自动更新（无需手动刷新）

## 4. 回归验证

- [x] 4.1 `cd apps/frontend_web && npm run build`
- [x] 4.2 `pytest -q`
