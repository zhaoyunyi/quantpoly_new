# 前端 API 客户端库（frontend_api_client）

## 1. 目标

本目录承载前端直连后端（HTTP + cookie session）的契约适配层（ACL），提供：

- `request()`：统一 `fetch` 封装（`baseUrl`、`credentials: include`、超时、JSON/文本响应、错误映射）
- `Envelope` 解包：适配后端 `success_response / error_response / paged_response`
- 最小 endpoints：`Auth / Users(Me) / Preferences / Health`
- React hooks：`AuthProvider / useAuth`
- CLI：健康检查与 CORS 探测（stdout 输出 JSON）

## 2. 使用方式（示例）

```ts
import { configureClient, AuthProvider } from '@qp/api-client'

configureClient({ baseUrl: 'http://localhost:8000' })

// 在应用入口包裹 <AuthProvider>，组件内使用 useAuth()
```

## 3. CLI

```bash
node libs/frontend_api_client/cli.mjs --backend http://localhost:8000
node libs/frontend_api_client/cli.mjs --backend http://localhost:8000 --probe cors --origin http://localhost:3300
```
