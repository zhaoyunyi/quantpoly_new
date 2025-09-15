## 1. 组合入口配置基座

- [x] 1.1 为组合入口增加 provider/persistence 运行时配置模型（含默认值与校验）
- [x] 1.2 在 `build_context` 中按配置注入仓储与 provider（禁止隐式降级）
- [x] 1.3 为非法配置增加 fail-fast 错误语义与测试

## 2. 持久化适配器接入

- [x] 2.1 为 `risk-control` 增加 sqlite 持久化仓储并接入组合入口
- [x] 2.2 为 `signal-execution` 增加 sqlite 持久化仓储并接入组合入口
- [x] 2.3 为 `user-preferences` 增加 sqlite 持久化适配器并接入组合入口

## 3. 行情 provider 运行时接入

- [x] 3.1 接入 `alpaca` provider 到组合入口装配
- [x] 3.2 保留 `inmemory` 作为开发/测试选项并显式标记
- [x] 3.3 为 provider 健康检查和启动配置增加测试

## 4. CLI 与验证

- [ ] 4.1 为新增配置能力补齐 CLI 入口（JSON 输入输出）
- [x] 4.2 增加 Given/When/Then 测试覆盖配置装配与重启后数据保持
- [x] 4.3 运行 `openspec validate update-runtime-persistence-provider-baseline --strict`
