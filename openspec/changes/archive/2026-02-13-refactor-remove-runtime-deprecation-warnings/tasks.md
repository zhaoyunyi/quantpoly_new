## 1. 弃用告警治理

- [x] 1.1 用 timezone-aware 方式替换 `datetime.utcnow()`
- [x] 1.2 移除 `argparse.FileType` 并改为路径参数读取
- [x] 1.3 增加无弃用告警回归测试

## 2. 验证

- [x] 2.1 运行 `libs/market_data/tests` 与 `libs/user_preferences/tests`
- [x] 2.2 运行全量 `pytest`
- [x] 2.3 运行 `openspec validate refactor-remove-runtime-deprecation-warnings --strict`
