# QuantPoly 文档入口（当前实现一致版）

> 本目录只保留与当前代码实现一致的文档。历史计划稿/盘点稿已移除。

## 1. 当前状态总览（先读）

- `docs/migration/2026-02-13-backend-current-state.md`

说明：用于确认“当前后端实际实现边界”，包括存储路径、核心上下文、门禁命令。

## 2. 运行与切换手册

- `docs/runbooks/backend-operations-runbook.md`
- `docs/runbooks/fullstack-coolify-deployment-runbook.md`

说明：包含发布/切换前后操作基线、冒烟命令、观测指标与回滚建议。

## 3. 门禁手册与样例

- `docs/gates/backend-gate-handbook.md`
- `docs/gates/examples/capability_gate_input.json`

说明：定义能力门禁与存储契约门禁的输入/输出与判定规则。

## 4. 前端建设文档

- `docs/frontend/AGENTS.md`

说明：前端目录、UI 规范、架构规范、设计令牌规范入口。

## 5. 快速命令

```bash
# 能力门禁
cat docs/gates/examples/capability_gate_input.json | python3 -m platform_core.cli capability-gate

# 存储契约防回流门禁
python3 -m platform_core.cli storage-contract-gate

# 组合入口冒烟
python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000
```
