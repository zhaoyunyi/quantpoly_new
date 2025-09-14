## 1. Provider 装配

- [ ] 1.1 在组合入口增加 market provider 配置读取
- [ ] 1.2 支持装配 alpaca provider 与 inmemory provider
- [ ] 1.3 非法 provider 配置 fail-fast

## 2. 语义与错误处理

- [ ] 2.1 统一 provider 初始化错误与上游错误码
- [ ] 2.2 校验 `provider-health` 返回字段与 provider 标识一致

## 3. 测试与验证

- [ ] 3.1 先写失败测试（Red）：alpaca 装配、非法 provider
- [ ] 3.2 覆盖 quote/history 在 provider 异常下的统一错误 envelope
- [ ] 3.3 运行 `openspec validate update-market-data-provider-runtime-parity --strict`
