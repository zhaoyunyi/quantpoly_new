# Wave 7 管理员治理上下文迁移 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 落地 `add-admin-governance-context-migration`：管理员动作目录、统一授权策略、二次确认令牌与结构化审计日志。

**Architecture:** 新建 `admin_governance` 库，提供治理策略引擎与审计存储；在 `signal_execution` 高风险接口（`cleanup-all`）接入治理检查器，替代业务路由内临时权限拼接。

**Tech Stack:** Python、pytest。

---

### Task 1: 治理内核红测与实现

- 动作目录（action catalog）
- 授权策略（role/level/policy）
- 确认令牌（短 TTL、单次使用）
- 审计日志（敏感字段脱敏）

### Task 2: 业务接入

- 在 `signal_execution` 的全局清理接口接入治理检查
- 普通用户统一返回 403
- 管理员需携带确认令牌才能执行高风险动作

### Task 3: 验证

- 越权回归测试
- 审计脱敏测试
- `pytest -q` + `openspec validate add-admin-governance-context-migration --strict`

