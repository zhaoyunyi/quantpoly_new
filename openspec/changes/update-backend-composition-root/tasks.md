## 1. 建立统一组合入口

- [x] 1.1 新建后端 app composition root（单一启动入口）
- [x] 1.2 统一注册所有 context 的 API Router 与 WS Endpoint
- [x] 1.3 建立按波次启停的模块开关机制

## 2. 统一横切能力

- [x] 2.1 统一鉴权依赖注入（Single CurrentUser）
- [x] 2.2 统一错误响应与错误码映射策略
- [x] 2.3 统一日志脱敏策略（headers/cookies/token/request body）

## 3. 切换与验证

- [x] 3.1 设计切换前冒烟校验脚本（REST + WS）
- [x] 3.2 设计切换后观察指标采集
- [x] 3.3 运行 `openspec validate update-backend-composition-root --strict`
