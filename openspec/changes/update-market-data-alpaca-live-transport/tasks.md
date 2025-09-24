## 1. Transport 与配置

- [x] 1.1 定义 alpaca transport 配置对象（key/secret/base-url/timeout）
- [x] 1.2 实现 transport 适配（search/quote/history）
- [x] 1.3 缺失配置时 fail-fast 并返回稳定错误码

## 2. 运行时与 CLI 装配

- [x] 2.1 组合入口按配置注入可运行 transport
- [x] 2.2 market-data CLI 支持 provider 与 transport 配置输入
- [x] 2.3 `provider-health` 输出真实 provider 运行状态

## 3. 错误语义与可观测

- [x] 3.1 统一超时、限流、鉴权失败错误映射
- [x] 3.2 增加调用耗时与失败原因观测字段（脱敏）
- [x] 3.3 更新运维文档与环境变量说明

## 4. 测试与验证

- [x] 4.1 先写失败测试（Red）：配置缺失、上游 401/429/timeout
- [x] 4.2 API/CLI 回归测试覆盖 quote/history/search
- [x] 4.3 运行 `openspec validate update-market-data-alpaca-live-transport --strict`
