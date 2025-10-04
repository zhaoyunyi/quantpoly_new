## 1. 鉴权输入规范收敛

- [x] 1.1 Red：legacy Bearer token 与 legacy cookie 鉴权失败
- [x] 1.2 Green：仅保留标准 Bearer/session_token 输入解析

## 2. API/CLI/WS 行为一致性

- [x] 2.1 user-auth CLI 对 legacy token 返回 `INVALID_TOKEN`
- [x] 2.2 monitoring WS 对 legacy cookie 返回未授权

## 3. 回归与规范验证

- [x] 3.1 回归 user-auth 与 monitoring-realtime 相关测试
- [x] 3.2 运行 `openspec validate remove-legacy-session-token-compat --strict`
