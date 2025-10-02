"""strategy_management FastAPI 路由。"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from job_orchestration.service import IdempotencyConflictError
from job_orchestration.service import JobOrchestrationService
from pydantic import BaseModel, Field

from platform_core.response import error_response, success_response
from strategy_management.domain import InvalidStrategyTransitionError, StrategyInUseError
from strategy_management.service import (
    InvalidPortfolioConstraintsError,
    InvalidPortfolioWeightsError,
    InvalidResearchParameterSpaceError,
    InvalidResearchStatusFilterError,
    InvalidStrategyParametersError,
    PortfolioAccessDeniedError,
    PortfolioMemberNotFoundError,
    StrategyAccessDeniedError,
    StrategyService,
)


class ResearchPerformanceTaskRequest(BaseModel):
    analysis_period_days: int = Field(default=30, alias="analysisPeriodDays", ge=1, le=365)
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


class ResearchOptimizationTaskRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    method: str = Field(default="grid")
    objective: dict[str, Any] = Field(default_factory=dict)
    parameter_space: dict[str, dict[str, Any]] = Field(default_factory=dict, alias="parameterSpace")
    constraints: dict[str, Any] = Field(default_factory=dict)
    budget: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}




class CreatePortfolioRequest(BaseModel):
    name: str
    constraints: dict[str, Any] = Field(default_factory=dict)


class UpdatePortfolioRequest(BaseModel):
    name: str | None = None
    constraints: dict[str, Any] | None = None


class PortfolioMemberRequest(BaseModel):
    strategy_id: str = Field(alias="strategyId")
    weight: float

    model_config = {"populate_by_name": True}


class PortfolioTaskRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    target_weights: dict[str, Any] = Field(default_factory=dict, alias="targetWeights")

    model_config = {"populate_by_name": True}


class CreateStrategyRequest(BaseModel):
    name: str
    template: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class UpdateStrategyRequest(BaseModel):
    name: str | None = None
    parameters: dict[str, Any] | None = None


class CreateStrategyFromTemplateRequest(BaseModel):
    name: str
    template_id: str = Field(alias="templateId")
    parameters: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ValidateExecutionRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


class CreateBacktestForStrategyRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")

    model_config = {"populate_by_name": True}


def _dt(value: datetime) -> str:
    return value.isoformat()


def _serialize_strategy(strategy) -> dict[str, Any]:
    return {
        "id": strategy.id,
        "userId": strategy.user_id,
        "name": strategy.name,
        "template": strategy.template,
        "parameters": strategy.parameters,
        "status": strategy.status,
        "createdAt": _dt(strategy.created_at),
        "updatedAt": _dt(strategy.updated_at),
    }


def _serialize_backtest(task: Any) -> dict[str, Any]:
    if isinstance(task, dict):
        return task

    return {
        "id": task.id,
        "userId": task.user_id,
        "strategyId": task.strategy_id,
        "status": task.status,
        "config": task.config,
        "metrics": task.metrics,
        "createdAt": _dt(task.created_at),
        "updatedAt": _dt(task.updated_at),
    }


def _serialize_portfolio(portfolio: Any) -> dict[str, Any]:
    if isinstance(portfolio, dict):
        return dict(portfolio)

    to_dict = getattr(portfolio, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())

    return {
        "id": str(getattr(portfolio, "id", "")),
        "userId": str(getattr(portfolio, "user_id", "")),
        "name": str(getattr(portfolio, "name", "")),
        "status": str(getattr(portfolio, "status", "draft")),
        "version": int(getattr(portfolio, "version", 1)),
        "constraints": dict(getattr(portfolio, "constraints", {})),
        "members": list(getattr(portfolio, "members", [])),
    }


def _access_denied_response() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=error_response(
            code="STRATEGY_ACCESS_DENIED",
            message="strategy does not belong to current user",
        ),
    )


def _portfolio_access_denied_response() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=error_response(
            code="PORTFOLIO_ACCESS_DENIED",
            message="portfolio does not belong to current user",
        ),
    )


def create_router(
    *,
    service: StrategyService,
    get_current_user: Any,
    job_service: JobOrchestrationService | None = None,
    signal_service: Any | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/strategies/templates")
    def list_templates(current_user=Depends(get_current_user)):
        del current_user
        return success_response(data=service.list_templates())

    @router.get("/strategies")
    def list_strategies(
        status: str | None = Query(default=None),
        search: str | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, alias="pageSize", ge=1, le=200),
        current_user=Depends(get_current_user),
    ):
        listing = service.query_strategies(
            user_id=current_user.id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
        )
        return success_response(
            data={
                "items": [_serialize_strategy(item) for item in listing["items"]],
                "total": int(listing["total"]),
                "page": int(listing["page"]),
                "pageSize": int(listing["pageSize"]),
            }
        )

    @router.get("/strategies/{strategy_id}")
    def get_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        strategy = service.get_strategy(user_id=current_user.id, strategy_id=strategy_id)
        if strategy is None:
            return _access_denied_response()
        return success_response(data=_serialize_strategy(strategy))

    @router.post("/strategies")
    def create_strategy(body: CreateStrategyRequest, current_user=Depends(get_current_user)):
        try:
            created = service.create_strategy(
                user_id=current_user.id,
                name=body.name,
                template=body.template,
                parameters=body.parameters,
            )
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(data=_serialize_strategy(created))

    @router.put("/strategies/{strategy_id}")
    def update_strategy(
        strategy_id: str,
        body: UpdateStrategyRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            updated = service.update_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
                name=body.name,
                parameters=body.parameters,
            )
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        if updated is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(updated))

    @router.post("/strategies/from-template")
    def create_strategy_from_template(
        body: CreateStrategyFromTemplateRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            created = service.create_strategy_from_template(
                user_id=current_user.id,
                name=body.name,
                template_id=body.template_id,
                parameters=body.parameters,
            )
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(data=_serialize_strategy(created))

    @router.post("/strategies/{strategy_id}/validate-execution")
    def validate_execution(
        strategy_id: str,
        body: ValidateExecutionRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            strategy = service.validate_execution_parameters(
                user_id=current_user.id,
                strategy_id=strategy_id,
                parameters=body.parameters,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()
        except InvalidStrategyParametersError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="STRATEGY_INVALID_PARAMETERS",
                    message=str(exc),
                ),
            )

        return success_response(
            data={
                "valid": True,
                "strategyId": strategy.id,
                "template": strategy.template,
            }
        )

    @router.post("/strategies/{strategy_id}/backtests")
    def create_strategy_backtest(
        strategy_id: str,
        body: CreateBacktestForStrategyRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            task = service.create_backtest_for_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
                config=body.config,
                idempotency_key=body.idempotency_key,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()

        return success_response(data=_serialize_backtest(task))

    @router.get("/strategies/{strategy_id}/backtests")
    def list_strategy_backtests(
        strategy_id: str,
        current_user=Depends(get_current_user),
        status: str | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, alias="pageSize", ge=1, le=200),
    ):
        try:
            listing = service.list_backtests_for_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
                status=status,
                page=page,
                page_size=page_size,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()

        items = [_serialize_backtest(item) for item in listing.get("items", [])]
        return success_response(
            data={
                "items": items,
                "total": int(listing.get("total", len(items))),
                "page": int(listing.get("page", page)),
                "pageSize": int(listing.get("pageSize", page_size)),
            }
        )

    @router.get("/strategies/{strategy_id}/backtest-stats")
    def strategy_backtest_stats(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            stats = service.backtest_stats_for_strategy(
                user_id=current_user.id,
                strategy_id=strategy_id,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()

        return success_response(data=stats)

    @router.post("/strategies/{strategy_id}/activate")
    def activate_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            strategy = service.activate_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except InvalidStrategyTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_INVALID_TRANSITION",
                    message=str(exc),
                ),
            )

        if strategy is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(strategy))

    @router.post("/strategies/{strategy_id}/deactivate")
    def deactivate_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            strategy = service.deactivate_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except InvalidStrategyTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_INVALID_TRANSITION",
                    message=str(exc),
                ),
            )

        if strategy is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(strategy))

    @router.post("/strategies/{strategy_id}/archive")
    def archive_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            strategy = service.archive_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except InvalidStrategyTransitionError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_INVALID_TRANSITION",
                    message=str(exc),
                ),
            )

        if strategy is None:
            return _access_denied_response()

        return success_response(data=_serialize_strategy(strategy))

    @router.delete("/strategies/{strategy_id}")
    def delete_strategy(strategy_id: str, current_user=Depends(get_current_user)):
        try:
            deleted = service.delete_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except StrategyInUseError as exc:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    code="STRATEGY_IN_USE",
                    message=str(exc),
                ),
            )

        if not deleted:
            return _access_denied_response()

        return success_response(data={"deleted": True})



    @router.get("/portfolios")
    def list_portfolios(current_user=Depends(get_current_user)):
        items = service.list_portfolios(user_id=current_user.id)
        return success_response(data=[_serialize_portfolio(item) for item in items])

    @router.get("/portfolios/{portfolio_id}")
    def get_portfolio(portfolio_id: str, current_user=Depends(get_current_user)):
        portfolio = service.get_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)
        if portfolio is None:
            return _portfolio_access_denied_response()
        return success_response(data=_serialize_portfolio(portfolio))

    @router.post("/portfolios")
    def create_portfolio(body: CreatePortfolioRequest, current_user=Depends(get_current_user)):
        try:
            created = service.create_portfolio(
                user_id=current_user.id,
                name=body.name,
                constraints=body.constraints,
            )
        except InvalidPortfolioConstraintsError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="PORTFOLIO_INVALID_CONSTRAINTS",
                    message=str(exc),
                ),
            )

        return success_response(data=_serialize_portfolio(created))

    @router.put("/portfolios/{portfolio_id}")
    def update_portfolio(
        portfolio_id: str,
        body: UpdatePortfolioRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            updated = service.update_portfolio(
                user_id=current_user.id,
                portfolio_id=portfolio_id,
                name=body.name,
                constraints=body.constraints,
            )
        except PortfolioAccessDeniedError:
            return _portfolio_access_denied_response()
        except InvalidPortfolioConstraintsError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="PORTFOLIO_INVALID_CONSTRAINTS",
                    message=str(exc),
                ),
            )
        except InvalidPortfolioWeightsError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="PORTFOLIO_INVALID_WEIGHTS",
                    message=str(exc),
                ),
            )

        return success_response(data=_serialize_portfolio(updated))

    @router.delete("/portfolios/{portfolio_id}")
    def delete_portfolio(portfolio_id: str, current_user=Depends(get_current_user)):
        deleted = service.delete_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)
        if not deleted:
            return _portfolio_access_denied_response()
        return success_response(data={"deleted": True})

    @router.post("/portfolios/{portfolio_id}/members")
    def add_portfolio_member(
        portfolio_id: str,
        body: PortfolioMemberRequest,
        current_user=Depends(get_current_user),
    ):
        try:
            portfolio = service.add_portfolio_member(
                user_id=current_user.id,
                portfolio_id=portfolio_id,
                strategy_id=body.strategy_id,
                weight=body.weight,
            )
        except PortfolioAccessDeniedError:
            return _portfolio_access_denied_response()
        except StrategyAccessDeniedError:
            return _access_denied_response()
        except InvalidPortfolioWeightsError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="PORTFOLIO_INVALID_WEIGHTS",
                    message=str(exc),
                ),
            )

        return success_response(data=_serialize_portfolio(portfolio))

    @router.delete("/portfolios/{portfolio_id}/members/{strategy_id}")
    def remove_portfolio_member(
        portfolio_id: str,
        strategy_id: str,
        current_user=Depends(get_current_user),
    ):
        try:
            portfolio = service.remove_portfolio_member(
                user_id=current_user.id,
                portfolio_id=portfolio_id,
                strategy_id=strategy_id,
            )
        except PortfolioAccessDeniedError:
            return _portfolio_access_denied_response()
        except PortfolioMemberNotFoundError:
            return JSONResponse(
                status_code=404,
                content=error_response(
                    code="PORTFOLIO_MEMBER_NOT_FOUND",
                    message="portfolio member not found",
                ),
            )

        return success_response(data=_serialize_portfolio(portfolio))

    def _portfolio_strategy_metrics(*, user_id: str, portfolio: Any) -> dict[str, dict[str, Any]]:
        if signal_service is None:
            raise RuntimeError("signal execution is not configured")

        metrics_by_strategy: dict[str, dict[str, Any]] = {}
        members = getattr(portfolio, "members", []) or []
        for member in members:
            strategy_id = str(getattr(member, "strategy_id", ""))
            if not strategy_id:
                continue
            metrics_by_strategy[strategy_id] = signal_service.performance_statistics(
                user_id=user_id,
                strategy_id=strategy_id,
            )
        return metrics_by_strategy

    @router.get("/portfolios/{portfolio_id}/read-model")
    def get_portfolio_read_model(portfolio_id: str, current_user=Depends(get_current_user)):
        if signal_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="SIGNAL_EXECUTION_UNAVAILABLE",
                    message="signal execution is not configured",
                ),
            )

        portfolio = service.get_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)
        if portfolio is None:
            return _portfolio_access_denied_response()

        strategy_metrics = _portfolio_strategy_metrics(user_id=current_user.id, portfolio=portfolio)
        read_model = service.build_portfolio_read_model(
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            strategy_metrics=strategy_metrics,
        )
        return success_response(data=read_model)

    @router.post("/portfolios/{portfolio_id}/evaluation-task")
    def submit_portfolio_evaluation_task(
        portfolio_id: str,
        body: PortfolioTaskRequest | None = None,
        current_user=Depends(get_current_user),
    ):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        if signal_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="SIGNAL_EXECUTION_UNAVAILABLE",
                    message="signal execution is not configured",
                ),
            )

        portfolio = service.get_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)
        if portfolio is None:
            return _portfolio_access_denied_response()

        strategy_metrics = _portfolio_strategy_metrics(user_id=current_user.id, portfolio=portfolio)
        evaluation_result = service.build_portfolio_evaluation_result(
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            strategy_metrics=strategy_metrics,
        )

        job_idempotency_key = (body.idempotency_key if body is not None else None) or f"portfolio-evaluation-task:{portfolio_id}:{uuid4()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="portfolio_evaluate",
                payload={
                    "portfolioId": portfolio_id,
                    "memberStrategyIds": [str(getattr(member, "strategy_id", "")) for member in (getattr(portfolio, "members", []) or [])],
                },
                idempotency_key=job_idempotency_key,
            )

            def _evaluation_runner(payload: dict[str, Any]) -> dict[str, Any]:
                result = dict(evaluation_result)
                result["portfolioId"] = str(payload.get("portfolioId") or portfolio_id)
                return result

            job = job_service.dispatch_job_with_callable(
                user_id=current_user.id,
                job_id=job.id,
                runner=_evaluation_runner,
            )
        except IdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )

        return success_response(
            data={
                "taskId": job.id,
                "taskType": job.task_type,
                "status": job.status,
                "result": job.result,
            }
        )

    @router.post("/portfolios/{portfolio_id}/rebalance-task")
    def submit_portfolio_rebalance_task(
        portfolio_id: str,
        body: PortfolioTaskRequest | None = None,
        current_user=Depends(get_current_user),
    ):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        if signal_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="SIGNAL_EXECUTION_UNAVAILABLE",
                    message="signal execution is not configured",
                ),
            )

        portfolio = service.get_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)
        if portfolio is None:
            return _portfolio_access_denied_response()

        strategy_metrics = _portfolio_strategy_metrics(user_id=current_user.id, portfolio=portfolio)
        try:
            rebalance_result = service.build_portfolio_rebalance_result(
                user_id=current_user.id,
                portfolio_id=portfolio_id,
                strategy_metrics=strategy_metrics,
                target_weights=(body.target_weights if body is not None else None),
            )
        except InvalidPortfolioWeightsError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="PORTFOLIO_INVALID_WEIGHTS",
                    message=str(exc),
                ),
            )

        job_idempotency_key = (body.idempotency_key if body is not None else None) or f"portfolio-rebalance-task:{portfolio_id}:{uuid4()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="portfolio_rebalance",
                payload={
                    "portfolioId": portfolio_id,
                    "targetWeights": rebalance_result.get("targetWeights", {}),
                },
                idempotency_key=job_idempotency_key,
            )

            def _rebalance_runner(payload: dict[str, Any]) -> dict[str, Any]:
                result = dict(rebalance_result)
                result["portfolioId"] = str(payload.get("portfolioId") or portfolio_id)
                result["targetWeights"] = dict(payload.get("targetWeights") or rebalance_result.get("targetWeights", {}))
                return result

            job = job_service.dispatch_job_with_callable(
                user_id=current_user.id,
                job_id=job.id,
                runner=_rebalance_runner,
            )
        except IdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )

        return success_response(
            data={
                "taskId": job.id,
                "taskType": job.task_type,
                "status": job.status,
                "result": job.result,
            }
        )


    @router.post("/strategies/{strategy_id}/research/performance-task")
    def submit_strategy_performance_task(
        strategy_id: str,
        body: ResearchPerformanceTaskRequest,
        current_user=Depends(get_current_user),
    ):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        try:
            owned = service.get_strategy(user_id=current_user.id, strategy_id=strategy_id)
        except StrategyAccessDeniedError:
            owned = None
        if owned is None:
            return _access_denied_response()

        if signal_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="SIGNAL_EXECUTION_UNAVAILABLE",
                    message="signal execution is not configured",
                ),
            )

        metrics = signal_service.performance_statistics(user_id=current_user.id, strategy_id=strategy_id)

        job_idempotency_key = body.idempotency_key or f"strategy-performance-task:{strategy_id}:{uuid4()}"

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="strategy_performance_analyze",
                payload={
                    "strategyId": strategy_id,
                    "analysisPeriodDays": body.analysis_period_days,
                    "metrics": metrics,
                },
                idempotency_key=job_idempotency_key,
            )

            def _performance_runner(payload: dict[str, Any]) -> dict[str, Any]:
                return {
                    "strategyId": str(payload.get("strategyId") or strategy_id),
                    "analysisPeriodDays": int(payload.get("analysisPeriodDays") or body.analysis_period_days),
                    "metrics": dict(payload.get("metrics") or metrics),
                }

            job = job_service.dispatch_job_with_callable(
                user_id=current_user.id,
                job_id=job.id,
                runner=_performance_runner,
            )
        except IdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(
            data={
                "taskId": job.id,
                "taskType": job.task_type,
                "status": job.status,
                "result": job.result,
            }
        )

    @router.post("/strategies/{strategy_id}/research/optimization-task")
    def submit_strategy_optimization_task(
        strategy_id: str,
        body: ResearchOptimizationTaskRequest | None = None,
        current_user=Depends(get_current_user),
    ):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        strategy = service.get_strategy(user_id=current_user.id, strategy_id=strategy_id)
        if strategy is None:
            return _access_denied_response()

        if signal_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="SIGNAL_EXECUTION_UNAVAILABLE",
                    message="signal execution is not configured",
                ),
            )

        metrics = signal_service.performance_statistics(user_id=current_user.id, strategy_id=strategy_id)

        try:
            optimization_result = service.build_research_optimization_result(
                user_id=current_user.id,
                strategy_id=strategy_id,
                metrics=metrics,
                objective=(body.objective if body is not None else None),
                parameter_space=(body.parameter_space if body is not None else None),
                constraints=(body.constraints if body is not None else None),
                method=(body.method if body is not None else None),
                budget=(body.budget if body is not None else None),
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()
        except InvalidResearchParameterSpaceError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="RESEARCH_INVALID_PARAMETER_SPACE",
                    message=str(exc),
                ),
            )

        job_idempotency_key = (
            (body.idempotency_key if body is not None else None)
            or f"strategy-optimization-task:{strategy_id}:{uuid4()}"
        )

        task_started_at = datetime.now()
        constraints_payload = optimization_result.get("constraints", {})
        constraints_keys = sorted(constraints_payload.keys()) if isinstance(constraints_payload, dict) else []

        try:
            job = job_service.submit_job(
                user_id=current_user.id,
                task_type="strategy_optimization_suggest",
                payload={
                    "strategyId": strategy_id,
                    "method": optimization_result.get("method", "grid"),
                    "version": optimization_result.get("version"),
                    "objective": optimization_result.get("objective", {}),
                    "parameterSpace": optimization_result.get("parameterSpace", {}),
                    "constraints": optimization_result.get("constraints", {}),
                    "budget": optimization_result.get("budget", {}),
                    "constraintsKeys": constraints_keys,
                },
                idempotency_key=job_idempotency_key,
            )

            def _optimization_runner(payload: dict[str, Any]) -> dict[str, Any]:
                task_latency_ms = max(0, int((datetime.now() - task_started_at).total_seconds() * 1000))
                optimization_result_with_meta = dict(optimization_result)
                optimization_result_with_meta["metadata"] = {
                    "taskLatencyMs": task_latency_ms,
                    "constraintsKeys": list(payload.get("constraintsKeys") or constraints_keys),
                    "inputEcho": {
                        "method": optimization_result.get("method", "grid"),
                        "objective": optimization_result.get("objective", {}),
                        "parameterSpace": optimization_result.get("parameterSpace", {}),
                        "budget": optimization_result.get("budget", {}),
                    },
                }
                return {"optimizationResult": optimization_result_with_meta}

            job = job_service.dispatch_job_with_callable(
                user_id=current_user.id,
                job_id=job.id,
                runner=_optimization_runner,
            )
        except IdempotencyConflictError:
            return JSONResponse(
                status_code=409,
                content=error_response(code="IDEMPOTENCY_CONFLICT", message="idempotency key already exists"),
            )
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content=error_response(code="TASK_EXECUTION_FAILED", message=str(exc)),
            )

        return success_response(
            data={
                "taskId": job.id,
                "taskType": job.task_type,
                "status": job.status,
                "result": job.result,
            }
        )

    @router.get("/strategies/{strategy_id}/research/results")
    def list_strategy_research_results(
        strategy_id: str,
        status: str | None = Query(default=None),
        method: str | None = Query(default=None),
        version: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=200),
        current_user=Depends(get_current_user),
    ):
        if job_service is None:
            return JSONResponse(
                status_code=503,
                content=error_response(
                    code="TASK_ORCHESTRATION_UNAVAILABLE",
                    message="job orchestration is not configured",
                ),
            )

        jobs = job_service.list_jobs(
            user_id=current_user.id,
            task_type="strategy_optimization_suggest",
        )

        try:
            listing = service.list_research_results(
                user_id=current_user.id,
                strategy_id=strategy_id,
                jobs=jobs,
                status=status,
                method=method,
                version=version,
                limit=limit,
            )
        except StrategyAccessDeniedError:
            return _access_denied_response()
        except InvalidResearchStatusFilterError as exc:
            return JSONResponse(
                status_code=422,
                content=error_response(
                    code="RESEARCH_INVALID_STATUS_FILTER",
                    message=str(exc),
                ),
            )

        return success_response(data=listing)

    return router
