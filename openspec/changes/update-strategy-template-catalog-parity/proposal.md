## Why

当前 `strategy-management` 的模板目录仅包含一个最小 `mean_reversion`，参数 schema 也偏“占位”。
但源项目与产品愿景要求策略中心至少覆盖多种内置策略（移动均线、布林带、RSI、MACD、动量等），并提供可校验的参数范围与默认值。

如果模板目录不补齐：

- 前端无法构建“零编程门槛”的策略配置体验；
- 下游 `signal-execution` / `backtest-runner` 无法基于统一 schema 做参数校验与可复算；
- 不同上下文会出现参数命名漂移，破坏通用语言。

## What Changes

- 扩展 `_TEMPLATE_CATALOG`：至少覆盖 `moving_average`、`bollinger_bands`、`rsi`、`macd`、`mean_reversion`、`momentum`。
- 为每个模板补齐：`templateId/name/requiredParameters/defaults`（或等价字段），并统一参数命名与边界。
- 策略创建/更新/从模板创建必须使用该 schema 进行参数校验，并返回稳定错误码。

## Impact

- Affected specs:
  - `strategy-management`
- Affected code:
  - `libs/strategy_management/*`
- Downstream dependencies:
  - `signal-execution`（策略参数校验、策略驱动生成）
  - `backtest-runner`（回测 config 与模板参数一致性）
