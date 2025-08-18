"""signal_execution 应用服务。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from signal_execution.domain import ExecutionRecord, TradingSignal
from signal_execution.repository import InMemorySignalRepository


class SignalAccessDeniedError(PermissionError):
    """信号不属于当前用户或无权访问。"""


class AdminRequiredError(PermissionError):
    """全局维护接口需要管理员权限。"""


class BatchIdempotencyConflictError(RuntimeError):
    """批处理幂等键冲突。"""


class InvalidSignalParametersError(ValueError):
    """信号参数校验失败。"""


class SignalExecutionService:
    def __init__(
        self,
        *,
        repository: InMemorySignalRepository,
        strategy_owner_acl: Callable[[str, str], bool],
        account_owner_acl: Callable[[str, str], bool],
        strategy_parameter_validator: Callable[[str, str, dict[str, Any]], None] | None = None,
        governance_checker: Callable[..., Any] | None = None,
    ) -> None:
        self._repository = repository
        self._strategy_owner_acl = strategy_owner_acl
        self._account_owner_acl = account_owner_acl
        self._strategy_parameter_validator = strategy_parameter_validator
        self._governance_checker = governance_checker

    def _assert_signal_acl(self, *, user_id: str, strategy_id: str, account_id: str) -> None:
        if not self._strategy_owner_acl(user_id, strategy_id):
            raise SignalAccessDeniedError("strategy does not belong to current user")
        if not self._account_owner_acl(user_id, account_id):
            raise SignalAccessDeniedError("account does not belong to current user")

    def _idempotency_fingerprint(self, *, signal_ids: list[str]) -> str:
        return "|".join(sorted(signal_ids))

    @staticmethod
    def _signal_stats(signals: list[TradingSignal]) -> dict[str, int]:
        return {
            "total": len(signals),
            "pending": sum(1 for item in signals if item.status == "pending"),
            "expired": sum(1 for item in signals if item.status == "expired"),
            "executed": sum(1 for item in signals if item.status == "executed"),
            "cancelled": sum(1 for item in signals if item.status == "cancelled"),
        }

    def validate_parameters(
        self,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        parameters: dict[str, Any],
    ) -> None:
        self._assert_signal_acl(user_id=user_id, strategy_id=strategy_id, account_id=account_id)
        if self._strategy_parameter_validator is None:
            return

        try:
            self._strategy_parameter_validator(user_id, strategy_id, parameters)
        except PermissionError as exc:
            raise SignalAccessDeniedError(str(exc)) from exc
        except ValueError as exc:
            raise InvalidSignalParametersError(str(exc)) from exc

    def create_signal(
        self,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        symbol: str,
        side: str,
        parameters: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> TradingSignal:
        if parameters is not None:
            self.validate_parameters(
                user_id=user_id,
                strategy_id=strategy_id,
                account_id=account_id,
                parameters=parameters,
            )
        else:
            self._assert_signal_acl(user_id=user_id, strategy_id=strategy_id, account_id=account_id)

        signal = TradingSignal.create(
            user_id=user_id,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            expires_at=expires_at,
        )
        self._repository.save_signal(signal)
        return signal

    def get_signal(self, *, user_id: str, signal_id: str) -> TradingSignal | None:
        return self._repository.get_signal(signal_id=signal_id, user_id=user_id)

    def get_signal_detail(self, *, user_id: str, signal_id: str) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        return signal

    def list_signals(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        account_id: str | None = None,
        symbol: str | None = None,
        status: str | None = None,
    ) -> list[TradingSignal]:
        return self._repository.list_signals(
            user_id=user_id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            status=status,
        )

    def list_pending_signals(self, *, user_id: str) -> list[TradingSignal]:
        return self.list_signals(user_id=user_id, status="pending")

    def list_expired_signals(self, *, user_id: str) -> list[TradingSignal]:
        return self.list_signals(user_id=user_id, status="expired")

    def search_signals(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        account_id: str | None = None,
        symbol: str | None = None,
        status: str | None = None,
    ) -> list[TradingSignal]:
        return self.list_signals(
            user_id=user_id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            status=status,
        )

    def signal_dashboard(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        account_id: str | None = None,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        signals = self.search_signals(
            user_id=user_id,
            keyword=keyword,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
        )
        overall = self._signal_stats(signals)

        by_account_group: dict[str, list[TradingSignal]] = {}
        for signal in signals:
            account_signals = by_account_group.setdefault(signal.account_id, [])
            account_signals.append(signal)

        by_account: list[dict[str, Any]] = []
        for key in sorted(by_account_group.keys()):
            item = {"accountId": key}
            item.update(self._signal_stats(by_account_group[key]))
            by_account.append(item)

        result = dict(overall)
        result["byAccount"] = by_account
        return result

    def execute_signal(
        self,
        *,
        user_id: str,
        signal_id: str,
        execution_metrics: dict[str, float] | None = None,
    ) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        if signal.status != "pending":
            return signal

        signal.execute()
        self._repository.save_signal(signal)
        self._repository.save_execution(
            ExecutionRecord.create(
                user_id=user_id,
                signal_id=signal.id,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                status="executed",
                metrics=execution_metrics,
            )
        )
        return signal

    def cancel_signal(self, *, user_id: str, signal_id: str) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        if signal.status != "pending":
            return signal

        signal.cancel()
        self._repository.save_signal(signal)
        self._repository.save_execution(
            ExecutionRecord.create(
                user_id=user_id,
                signal_id=signal.id,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                status="cancelled",
            )
        )
        return signal

    def _run_batch(
        self,
        *,
        user_id: str,
        signal_ids: list[str],
        action: str,
        idempotency_key: str | None = None,
    ) -> dict:
        if idempotency_key:
            fingerprint = self._idempotency_fingerprint(signal_ids=signal_ids)
            existed = self._repository.get_batch_record(
                user_id=user_id,
                action=action,
                idempotency_key=idempotency_key,
            )
            if existed is not None:
                stored_fingerprint, stored_result = existed
                if stored_fingerprint != fingerprint:
                    raise BatchIdempotencyConflictError("idempotency key already exists")
                replay = dict(stored_result)
                replay["idempotent"] = True
                return replay
        else:
            fingerprint = ""

        results: list[dict] = []
        success = 0
        skipped = 0
        denied = 0

        for signal_id in signal_ids:
            signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
            if signal is None:
                denied += 1
                results.append({"signalId": signal_id, "status": "denied"})
                continue

            try:
                self._assert_signal_acl(
                    user_id=user_id,
                    strategy_id=signal.strategy_id,
                    account_id=signal.account_id,
                )
            except SignalAccessDeniedError:
                denied += 1
                results.append({"signalId": signal_id, "status": "denied"})
                continue

            if action == "execute":
                if signal.status == "pending":
                    self.execute_signal(user_id=user_id, signal_id=signal_id)
                    success += 1
                    results.append({"signalId": signal_id, "status": "executed"})
                else:
                    skipped += 1
                    results.append({"signalId": signal_id, "status": "skipped"})
            else:
                if signal.status == "pending":
                    self.cancel_signal(user_id=user_id, signal_id=signal_id)
                    success += 1
                    results.append({"signalId": signal_id, "status": "cancelled"})
                else:
                    skipped += 1
                    results.append({"signalId": signal_id, "status": "skipped"})

        if action == "execute":
            result = {
                "total": len(signal_ids),
                "executed": success,
                "skipped": skipped,
                "denied": denied,
                "results": results,
                "idempotent": False,
            }
        else:
            result = {
                "total": len(signal_ids),
                "cancelled": success,
                "skipped": skipped,
                "denied": denied,
                "results": results,
                "idempotent": False,
            }

        if idempotency_key:
            self._repository.save_batch_record(
                user_id=user_id,
                action=action,
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                result=result,
            )
        return result

    def batch_execute_signals(
        self,
        *,
        user_id: str,
        signal_ids: list[str],
        idempotency_key: str | None = None,
    ) -> dict:
        return self._run_batch(
            user_id=user_id,
            signal_ids=signal_ids,
            action="execute",
            idempotency_key=idempotency_key,
        )

    def batch_cancel_signals(
        self,
        *,
        user_id: str,
        signal_ids: list[str],
        idempotency_key: str | None = None,
    ) -> dict:
        return self._run_batch(
            user_id=user_id,
            signal_ids=signal_ids,
            action="cancel",
            idempotency_key=idempotency_key,
        )

    def list_executions(
        self,
        *,
        user_id: str,
        signal_id: str | None = None,
        status: str | None = None,
    ) -> list[ExecutionRecord]:
        return self._repository.list_executions(user_id=user_id, signal_id=signal_id, status=status)

    def get_execution(self, *, user_id: str, execution_id: str) -> ExecutionRecord:
        execution = self._repository.get_execution(execution_id=execution_id, user_id=user_id)
        if execution is None:
            raise SignalAccessDeniedError("signal does not belong to current user")
        return execution

    def list_running_executions(self, *, user_id: str) -> list[TradingSignal]:
        signals = self._repository.list_signals(user_id=user_id)
        return [item for item in signals if item.status in {"pending", "running"}]

    def execution_trend(self, *, user_id: str) -> dict:
        executions = self._repository.list_executions(user_id=user_id)
        return {
            "total": len(executions),
            "executed": sum(1 for item in executions if item.status == "executed"),
            "cancelled": sum(1 for item in executions if item.status == "cancelled"),
            "expired": sum(1 for item in executions if item.status == "expired"),
        }

    def performance_statistics(
        self,
        *,
        user_id: str,
        strategy_id: str | None = None,
        symbol: str | None = None,
    ) -> dict:
        executions = self._repository.list_executions(user_id=user_id, status="executed")
        if strategy_id is not None:
            executions = [item for item in executions if item.strategy_id == strategy_id]
        if symbol is not None:
            executions = [item for item in executions if item.symbol == symbol]

        pnls = [float(item.metrics.get("pnl", 0.0)) for item in executions if "pnl" in item.metrics]
        latencies = [
            float(item.metrics.get("latencyMs", 0.0)) for item in executions if "latencyMs" in item.metrics
        ]

        def _avg(values: list[float]) -> float:
            if not values:
                return 0.0
            return round(sum(values) / len(values), 4)

        return {
            "totalExecutions": len(executions),
            "averagePnl": _avg(pnls),
            "averageLatencyMs": _avg(latencies),
        }

    def cleanup_signals(self, *, user_id: str) -> int:
        return self._repository.delete_signals_by_user(user_id=user_id)

    def update_expired_signals(self, *, user_id: str, now: datetime | None = None) -> int:
        now_ts = now or datetime.now(timezone.utc)
        signals = self._repository.list_signals(user_id=user_id)
        expired_count = 0
        for signal in signals:
            if signal.status != "pending":
                continue
            if signal.expires_at is None or signal.expires_at > now_ts:
                continue
            signal.expire()
            expired_count += 1
            self._repository.save_signal(signal)
            self._repository.save_execution(
                ExecutionRecord.create(
                    user_id=user_id,
                    signal_id=signal.id,
                    strategy_id=signal.strategy_id,
                    symbol=signal.symbol,
                    status="expired",
                )
            )
        return expired_count

    def cleanup_expired_signals(self, *, user_id: str) -> int:
        return self._repository.delete_expired_signals_by_user(user_id=user_id)

    def cleanup_all_signals(
        self,
        *,
        user_id: str,
        is_admin: bool,
        admin_decision_source: str = "unknown",
        confirmation_token: str | None = None,
    ) -> int:
        if self._governance_checker is not None:
            role = "admin" if is_admin else "user"
            level = 10 if is_admin else 1
            try:
                self._governance_checker(
                    actor_id=user_id,
                    role=role,
                    level=level,
                    action="signals.cleanup_all",
                    target="signals",
                    confirmation_token=confirmation_token,
                    context={
                        "actor": user_id,
                        "token": confirmation_token or "",
                        "adminDecisionSource": admin_decision_source,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                raise AdminRequiredError(str(exc)) from exc
        elif not is_admin:
            raise AdminRequiredError("admin role required")

        return self._repository.delete_all_signals()
