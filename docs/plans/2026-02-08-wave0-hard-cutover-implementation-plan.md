# Wave0 Hard Cutover Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在允许 breaking change 的前提下，完成 Wave0 基座建设（能力门禁、统一组合入口、持久化与事务骨架），为后续业务波次提供“功能不缺失”的硬切换能力。

**Architecture:** 采用“三件套”基座先行：`capability baseline gates` 负责放行/阻断，`composition root` 负责统一装配与切换，`persistence + UoW` 负责数据一致性与可恢复。实现遵循 bounded context，不回退到单体业务路由。

**Tech Stack:** Python, FastAPI, Pydantic v2, OpenSpec, pytest, PostgreSQL/SQLite(D1边界)

---

### Task 1: 固化能力门禁数据结构与校验入口

**Files:**
- Create: `docs/plans/2026-02-08-capability-baseline-matrix.md`
- Modify: `openspec/changes/add-capability-baseline-gates/tasks.md`
- Test: `tests/gates/test_capability_baseline_gate.py`

**Step 1: Write the failing test**

```python
def test_gate_blocks_when_critical_capability_missing():
    matrix = {"auth_login": False}
    result = evaluate_gate(matrix)
    assert result.allowed is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/gates/test_capability_baseline_gate.py::test_gate_blocks_when_critical_capability_missing -v`
Expected: FAIL with `evaluate_gate` not found

**Step 3: Write minimal implementation**

```python
def evaluate_gate(matrix: dict):
    return GateResult(allowed=all(matrix.values()))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/gates/test_capability_baseline_gate.py::test_gate_blocks_when_critical_capability_missing -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/plans/2026-02-08-capability-baseline-matrix.md openspec/changes/add-capability-baseline-gates/tasks.md tests/gates/test_capability_baseline_gate.py
git cnd -m "feat: add capability baseline gate skeleton"
```

### Task 2: 建立统一组合入口骨架

**Files:**
- Create: `apps/backend_app/app.py`
- Create: `apps/backend_app/router_registry.py`
- Modify: `openspec/changes/update-backend-composition-root/tasks.md`
- Test: `tests/composition/test_router_registry.py`

**Step 1: Write the failing test**

```python
def test_composition_root_registers_all_contexts():
    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/ws/monitor" in paths
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/composition/test_router_registry.py::test_composition_root_registers_all_contexts -v`
Expected: FAIL with `create_app` not found

**Step 3: Write minimal implementation**

```python
def create_app():
    app = FastAPI()
    register_all_routes(app)
    return app
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/composition/test_router_registry.py::test_composition_root_registers_all_contexts -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/backend_app/app.py apps/backend_app/router_registry.py openspec/changes/update-backend-composition-root/tasks.md tests/composition/test_router_registry.py
git cnd -m "feat: add backend composition root skeleton"
```

### Task 3: 引入 UoW 协议与持久化适配器接口

**Files:**
- Create: `libs/platform_core/platform_core/uow.py`
- Create: `libs/trading_account/trading_account/repository_postgres.py`
- Create: `libs/backtest_runner/backtest_runner/repository_postgres.py`
- Modify: `openspec/changes/update-persistence-adapters-uow/tasks.md`
- Test: `libs/trading_account/tests/test_uow_contract.py`

**Step 1: Write the failing test**

```python
def test_uow_rolls_back_on_error():
    with pytest.raises(RuntimeError):
        with uow:
            repo.save(entity)
            raise RuntimeError("boom")
    assert repo.count() == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest libs/trading_account/tests/test_uow_contract.py::test_uow_rolls_back_on_error -v`
Expected: FAIL with `uow` fixture/protocol not found

**Step 3: Write minimal implementation**

```python
class UnitOfWork(Protocol):
    def __enter__(self): ...
    def __exit__(self, exc_type, exc, tb): ...
```

**Step 4: Run test to verify it passes**

Run: `pytest libs/trading_account/tests/test_uow_contract.py::test_uow_rolls_back_on_error -v`
Expected: PASS

**Step 5: Commit**

```bash
git add libs/platform_core/platform_core/uow.py libs/trading_account/trading_account/repository_postgres.py libs/backtest_runner/backtest_runner/repository_postgres.py openspec/changes/update-persistence-adapters-uow/tasks.md libs/trading_account/tests/test_uow_contract.py
git cnd -m "feat: add uow protocol and persistence adapter skeleton"
```

### Task 4: 增加幂等冲突语义与验证

**Files:**
- Modify: `libs/job_orchestration/job_orchestration/service.py`
- Create: `libs/job_orchestration/tests/test_idempotency_conflict_semantics.py`
- Modify: `openspec/changes/update-persistence-adapters-uow/specs/job-orchestration/spec.md`

**Step 1: Write the failing test**

```python
def test_duplicate_idempotency_key_returns_conflict_semantics():
    service.submit_job(user_id="u1", task_type="backtest_run", payload={}, idempotency_key="k1")
    with pytest.raises(IdempotencyConflictError):
        service.submit_job(user_id="u1", task_type="backtest_run", payload={}, idempotency_key="k1")
```

**Step 2: Run test to verify it fails**

Run: `pytest libs/job_orchestration/tests/test_idempotency_conflict_semantics.py::test_duplicate_idempotency_key_returns_conflict_semantics -v`
Expected: FAIL (missing test/behavior)

**Step 3: Write minimal implementation**

```python
if exists is not None:
    raise IdempotencyConflictError("idempotency key already exists")
```

**Step 4: Run test to verify it passes**

Run: `pytest libs/job_orchestration/tests/test_idempotency_conflict_semantics.py::test_duplicate_idempotency_key_returns_conflict_semantics -v`
Expected: PASS

**Step 5: Commit**

```bash
git add libs/job_orchestration/job_orchestration/service.py libs/job_orchestration/tests/test_idempotency_conflict_semantics.py openspec/changes/update-persistence-adapters-uow/specs/job-orchestration/spec.md
git cnd -m "feat: enforce idempotency conflict semantics"
```

### Task 5: Wave0 切换前全量校验

**Files:**
- Modify: `docs/plans/2026-02-08-wave0-hard-cutover-implementation-plan.md`
- Modify: `openspec/changes/add-capability-baseline-gates/tasks.md`

**Step 1: Run OpenSpec strict validation**

Run: `openspec validate --changes --strict`
Expected: PASS for all active changes

**Step 2: Run focused tests**

Run: `pytest libs/job_orchestration/tests libs/trading_account/tests -q`
Expected: PASS

**Step 3: Run full regression**

Run: `pytest -q`
Expected: PASS（允许已有明确标记的 deselected 项）

**Step 4: Commit**

```bash
git add docs/plans/2026-02-08-wave0-hard-cutover-implementation-plan.md openspec/changes/add-capability-baseline-gates/tasks.md
git cnd -m "chore: validate wave0 hard cutover baseline"
```
