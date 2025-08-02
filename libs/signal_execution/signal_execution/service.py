"""signal_execution 应用服务。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from signal_execution.domain import ExecutionRecord, TradingSignal
from signal_execution.repository import InMemorySignalRepository


class SignalAccessDeniedError(PermissionError):
    """信号不属于当前用户或无权访问。"""


class AdminRequiredError(PermissionError):
    """全局维护接口需要管理员权限。"""


class SignalExecutionService:
    def __init__(
        self,
        *,
        repository: InMemorySignalRepository,
        strategy_owner_acl: Callable[[str, str], bool],
        account_owner_acl: Callable[[str, str], bool],
        governance_checker: Callable[..., Any] | None = None,
    ) -> None:
        self._repository = repository
        self._strategy_owner_acl = strategy_owner_acl
        self._account_owner_acl = account_owner_acl
        self._governance_checker = governance_checker

    def _assert_signal_acl(self, *, user_id: str, strategy_id: str, account_id: str) -> None:
        if not self._strategy_owner_acl(user_id, strategy_id):
            raise SignalAccessDeniedError("strategy does not belong to current user")
        if not self._account_owner_acl(user_id, account_id):
            raise SignalAccessDeniedError("account does not belong to current user")

    def create_signal(
        self,
        *,
        user_id: str,
        strategy_id: str,
        account_id: str,
        symbol: str,
        side: str,
    ) -> TradingSignal:
        self._assert_signal_acl(user_id=user_id, strategy_id=strategy_id, account_id=account_id)
        signal = TradingSignal.create(
            user_id=user_id,
            strategy_id=strategy_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
        )
        self._repository.save_signal(signal)
        return signal

    def get_signal(self, *, user_id: str, signal_id: str) -> TradingSignal | None:
        return self._repository.get_signal(signal_id=signal_id, user_id=user_id)

    def list_signals(self, *, user_id: str, keyword: str | None = None) -> list[TradingSignal]:
        return self._repository.list_signals(user_id=user_id, keyword=keyword)

    def execute_signal(self, *, user_id: str, signal_id: str) -> TradingSignal:
        signal = self._repository.get_signal(signal_id=signal_id, user_id=user_id)
        if signal is None:
            raise SignalAccessDeniedError("signal does not belong to current user")

        self._assert_signal_acl(
            user_id=user_id,
            strategy_id=signal.strategy_id,
            account_id=signal.account_id,
        )
        signal.execute()
        self._repository.save_signal(signal)
        self._repository.save_execution(
            ExecutionRecord.create(user_id=user_id, signal_id=signal.id, status="executed")
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
        signal.cancel()
        self._repository.save_signal(signal)
        self._repository.save_execution(
            ExecutionRecord.create(user_id=user_id, signal_id=signal.id, status="cancelled")
        )
        return signal

    def execution_trend(self, *, user_id: str) -> dict:
        executions = self._repository.list_executions(user_id=user_id)
        return {
            "total": len(executions),
            "executed": sum(1 for item in executions if item.status == "executed"),
            "cancelled": sum(1 for item in executions if item.status == "cancelled"),
        }

    def cleanup_signals(self, *, user_id: str) -> int:
        return self._repository.delete_signals_by_user(user_id=user_id)

    def cleanup_all_signals(
        self,
        *,
        user_id: str,
        is_admin: bool,
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
                    context={"actor": user_id},
                )
            except Exception as exc:  # noqa: BLE001
                raise AdminRequiredError(str(exc)) from exc
        elif not is_admin:
            raise AdminRequiredError("admin role required")

        return self._repository.delete_all_signals()
