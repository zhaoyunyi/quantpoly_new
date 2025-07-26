# update-backend-user-ownership 落地记录（TDD + OpenSpec）

## 目标

- 提供可复用的资源所有权（ownership）校验能力（library-first）
- 通过可执行测试覆盖：按 user_id 过滤、越权返回 403
- 完成 OpenSpec 归档（archive）流程，将 capability 写入主规格 `openspec/specs/`

## 落地内容

### 1) Ownership library

- `libs/platform_core/platform_core/ownership.py`
  - `OwnershipViolationError`
  - `InMemoryOwnedResourceRepository`：所有对外方法显式接收 `user_id`（含 `update()`）

### 2) FastAPI 403 映射辅助

- `libs/platform_core/platform_core/fastapi/ownership.py`
  - `raise_ownership_forbidden()`：统一抛 HTTP 403

### 3) 测试用例

- `libs/platform_core/tests/test_ownership.py`
  - list 仅返回本人资源
  - get/patch/delete 越权返回 403

## OpenSpec 流程

- 变更归档后位置：`openspec/changes/archive/2026-02-08-update-backend-user-ownership/`
- 主规格输出：`openspec/specs/backend-user-ownership/spec.md`

## 验证命令

```bash
pytest -q
openspec validate --all --strict
```
