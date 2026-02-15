## 1. Spec Delta

- [x] 1.1 更新 `market-data`：实时流鉴权回调必须使用显式 `request` 签名，禁止 legacy 回退。
- [x] 1.2 运行 `openspec validate remove-legacy-market-data-ws-auth-signature-adapter --strict`

## 2. Red

- [x] 2.1 新增测试：传入旧签名 `get_current_user()` 时，`create_router` 必须拒绝（fail-fast）

## 3. Green

- [x] 3.1 在 `market_data` router 初始化阶段对 `get_current_user` 做签名校验（要求 `request`）
- [x] 3.2 移除 `_resolve_ws_current_user` 的 `TypeError` 回退，统一使用 `get_current_user(request=...)`
- [x] 3.3 更新 `market_data` 测试中的鉴权桩函数签名

## 4. 回归与归档

- [x] 4.1 运行 `ruff check .`
- [x] 4.2 运行 `pytest -q`
- [x] 4.3 使用 `git cnd` 提交
- [x] 4.4 执行 `openspec archive remove-legacy-market-data-ws-auth-signature-adapter --yes`
