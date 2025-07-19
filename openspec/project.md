# Project Context

## Purpose
QuantPoly 是一个量化交易平台，目标能力包括：

- 用户系统（认证、会话、权限、偏好设置）
- 策略管理（CRUD、模板、版本）
- 回测（任务调度、结果与指标、对比）
- 交易账户与交易执行（纸上/实盘、资金/持仓/流水）
- 风控与风险评估（规则、告警、建议）
- 实时监控（WebSocket/SSE、signals/alerts 推送）

本仓库用于以 **OpenSpec + DDD + Library-First** 的方式，从旧项目逐步迁移/重构后端能力。

## Tech Stack（拟）
> 说明：旧项目后端为 FastAPI + SQLModel；迁移阶段尽量保持技术栈一致，避免无谓重写。

- Python（FastAPI / Pydantic v2 / SQLAlchemy/SQLModel）
- PostgreSQL：业务/计算数据（交易、回测、信号、风控、行情等）
- SQLite / Cloudflare D1：用户与轻量配置数据（是否继续保留 D1 由认证方案决定）
- Redis + Celery（或等价队列）：异步任务（回测、策略执行、风控批处理）

## Project Conventions

### Code Style
- Python：`snake_case` 函数/模块，`PascalCase` 类；类型标注完整，避免隐式 `Any`。
- API 字段：对外响应统一 `camelCase`；数据库字段保持 `snake_case`，通过 alias 映射。

### Architecture Patterns
- 严格遵守 `spec/DDDSpec.md`：通用语言、限界上下文、聚合根与充血模型。
- 严格遵守 `spec/ProgramSpec.md`：
  - **Library-First**：每个能力先实现为可复用库
  - **CLI Mandate**：每个库必须提供 CLI
  - **Test-First**：严格 TDD（先红后绿）

### Testing Strategy
- 单元测试优先，pytest 为主。
- BDD 表达与输出格式遵守 `spec/BDD_TestSpec.md`。

### Git Workflow
- 必须使用 `git cnd` 提交（见根目录 `AGENTS.md`）。

## Domain Context（通用语言草案）
- User：用户（身份、会话、偏好）
- Strategy：策略（参数、状态、归属用户）
- Backtest：回测（配置、任务、结果、指标）
- TradingAccount：交易账户（资金、持仓、流水）
- TradeRecord / CashFlow：成交记录 / 资金流水
- RiskRule / RiskAssessment / Alert：风控规则 / 风险评估 / 告警
- TradingSignal：交易信号

## Important Constraints
- **用户系统相关能力必须聚合到后端**：前端不得再承担“用户数据库/会话签发/权限判断”等职责，只能作为 UI 与 API 调用方。
- 迁移期允许存在兼容层，但必须有清晰的弃用路径（deprecation plan）。

## External Dependencies
- Alpaca（行情/交易 API）
- Cloudflare D1（如保留）：生产环境通过 REST API 访问会带来一致性/延迟约束
