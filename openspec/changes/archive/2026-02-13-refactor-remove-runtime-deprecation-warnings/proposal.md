## Why

当前全量测试仍出现已知弃用告警：
- `market_data.api` 使用 `datetime.utcnow()`；
- `user_preferences.cli` 使用 `argparse.FileType`。

这些告警会增加 CI 噪音并影响后续 Python 版本升级稳定性。

## What Changes

- 将流网关时间戳生成切换为 timezone-aware UTC 写法；
- 替换 `argparse.FileType`，改为解析后手动读取文件路径；
- 增加无弃用告警的回归测试。

## Impact

- 影响 capability：`platform-core`（跨上下文运行质量约束）
- 影响代码：`market_data`、`user_preferences`
- 兼容性：不改变对外协议语义，仅消除运行时弃用告警
