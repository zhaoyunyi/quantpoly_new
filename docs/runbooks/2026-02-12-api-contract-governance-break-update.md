# API 契约治理（P1）：响应 Envelope 与用户路由 Break Update 说明

> 日期：2026-02-12

本文是给前端/调用方的迁移说明与冒烟要点。

## 1. 背景

在 Wave0~Wave7 完成“后端功能迁移并归档”后，当前仓库进入 **P1 契约治理** 阶段：

- 允许 **break update**（不追求旧接口兼容）
- 但要求 **功能不能缺失**
- 优先消除“同一能力在不同运行形态（组合入口 vs standalone app）契约不一致”的问题

本轮治理包含三项（均已归档到 `openspec/changes/archive/2026-02-12-*`，并已应用到 `openspec/specs/`）：

1. 错误响应 envelope 统一
2. 成功响应 envelope 统一
3. 用户 `me` 资源路由语义统一

## 2. 统一响应 Envelope（对外 API）

### 2.1 成功响应（success_response）

标准结构：

```json
{
  "success": true,
  "message": "ok",
  "data": {"...": "..."}
}
```

约定：

- `message` 始终存在（默认 `ok`）。
- 当接口本身不需要返回数据时，`data` 字段 **可能不存在**（而不是 `null`）。

### 2.2 错误响应（error_response）

标准结构：

```json
{
  "success": false,
  "error": {
    "code": "SOME_ERROR_CODE",
    "message": "human readable message"
  }
}
```

约定：

- HTTP status code 仍用于表达语义（401/403/404/409/422/5xx）。
- 业务/权限/校验错误都统一落入 `error.code`，调用方不得再依赖 FastAPI 默认的 `detail` 结构。

### 2.3 分页响应（paged_response）

标准结构：

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "pageSize": 20
  }
}
```

## 3. 用户系统路由 Break Update

### 3.1 `GET /auth/me` 已移除

- 旧端点：`GET /auth/me`
- 新端点：`GET /users/me`

当前行为：

- `GET /auth/me` 返回 `410 Gone`
- 错误 envelope：

```json
{
  "success": false,
  "error": {
    "code": "ROUTE_REMOVED",
    "message": "GET /auth/me has been removed; use GET /users/me"
  }
}
```

### 3.2 `/users/me` 资源语义收敛

以下端点属于“当前用户资源（me）”的权威路径：

- `GET /users/me`：读取当前用户
- `PATCH /users/me`：更新资料（displayName/email 等）
- `PATCH /users/me/password`：修改密码
- `DELETE /users/me`：自助注销/删除

## 4. 调用方迁移清单（前端/脚本/第三方）

1. **统一错误解析**：
   - 不再读取 `resp.json().detail`
   - 改为读取 `resp.json().error.code` 与 `resp.json().error.message`
2. **更新 `me` 查询路由**：
   - `/auth/me` → `/users/me`
3. **健壮处理无 data 的成功响应**：
   - `success=true` 不等价于 `data` 一定存在
4. **保持 HTTP status 的使用**：
   - 401 未认证 / 403 禁止 / 422 校验失败 / 409 冲突

## 5. 冒烟建议

组合入口切换/发布前，可执行：

```bash
python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000
```

人工额外验证建议（重点关注 break update 变更点）：

1. 登录后调用 `GET /users/me` 成功
2. 调用 `GET /auth/me` 返回 410 且 `error.code=ROUTE_REMOVED`
3. 任意鉴权失败返回 `{"success":false,"error":{...}}`（而非 `detail`）

