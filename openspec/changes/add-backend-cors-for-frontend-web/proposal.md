# Change: 为前端直连后端提供 CORS 支持（含 credentials）

## Why

当前前端将采用浏览器端 **HTTP 直连后端** 的方式对接现有 FastAPI 组合入口。若无 CORS 配置，浏览器将阻止跨 Origin 的 API 调用，且无法在跨域请求中携带 `session_token` cookie（credentials）。

## What Changes

- 在 `apps/backend_app` 组合入口安装 CORS middleware，支持：
  - 按配置白名单允许前端 origin（禁止 `*`）
  - `allow_credentials=true` 以支持 cookie session
  - 覆盖 `OPTIONS` 预检请求
- 新增可配置项（环境变量/设置项）以管理允许的 origins、methods、headers
- 增加回归测试，确保：
  - 预检请求返回正确的 CORS 响应头
  - 带 `credentials` 的请求可成功访问受保护端点（在测试中模拟）

## Impact

- Affected code:
  - `apps/backend_app/app.py`
  - `apps/backend_app/settings.py`
  - 相关测试文件（新增）
- Affected specs:
  - 新增 capability：`backend-cors`
- Risk:
  - CORS 误配可能导致跨站请求风险或前端无法登录（cookie 不被接受）
  - 需要明确 dev/prod 的 origin 列表与 cookie 策略（SameSite/secure）

