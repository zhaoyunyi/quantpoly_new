## 1. 实时通道协议

- [ ] 1.1 扩展 WebSocket 消息 envelope 与类型定义
- [ ] 1.2 实现 `ping/pong` 与订阅协议处理
- [ ] 1.3 增加连接恢复与增量快照逻辑

## 2. 数据推送与权限

- [ ] 2.1 接入 signals 与 alerts 推送源
- [ ] 2.2 推送前执行用户可访问账户过滤
- [ ] 2.3 增加重复消息去重与快照截断策略

## 3. 安全与验证

- [ ] 3.1 认证失败日志全量脱敏（header/cookie/body）
- [ ] 3.2 增加 WebSocket 鉴权与订阅行为测试
- [ ] 3.3 运行 `pytest -q` 与 `openspec validate update-monitoring-realtime-full-streaming --strict`

