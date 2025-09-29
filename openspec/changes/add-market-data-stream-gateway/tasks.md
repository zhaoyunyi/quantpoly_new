## 1. 流网关模型

- [x] 1.1 定义流订阅协议与事件 envelope
- [x] 1.2 定义连接生命周期与鉴权校验
- [x] 1.3 定义限流与退化（degraded）语义

## 2. API/CLI 能力

- [x] 2.1 新增 `/market/stream` 实时订阅入口
- [x] 2.2 增加订阅管理命令（CLI）用于本地验证
- [x] 2.3 增加 provider 健康与流状态观测接口

## 3. 测试与验证

- [x] 3.1 Red：鉴权失败、超限、非法订阅
- [x] 3.2 Green：连接、订阅、退订与事件推送
- [x] 3.3 运行 `openspec validate add-market-data-stream-gateway --strict`
