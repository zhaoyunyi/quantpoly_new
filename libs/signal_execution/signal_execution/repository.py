"""signal_execution in-memory 仓储。"""

from __future__ import annotations

from signal_execution.domain import ExecutionRecord, TradingSignal


class InMemorySignalRepository:
    def __init__(self) -> None:
        self._signals: dict[str, TradingSignal] = {}
        self._executions: dict[str, ExecutionRecord] = {}
        self._batch_records: dict[tuple[str, str, str], tuple[str, dict]] = {}

    def save_signal(self, signal: TradingSignal) -> None:
        self._signals[signal.id] = signal

    def get_signal(self, *, signal_id: str, user_id: str) -> TradingSignal | None:
        item = self._signals.get(signal_id)
        if item is None or item.user_id != user_id:
            return None
        return item

    def get_signal_any(self, *, signal_id: str) -> TradingSignal | None:
        return self._signals.get(signal_id)

    def list_signals(
        self,
        *,
        user_id: str,
        keyword: str | None = None,
        strategy_id: str | None = None,
        symbol: str | None = None,
        status: str | None = None,
    ) -> list[TradingSignal]:
        keyword_lower = keyword.lower() if keyword else None

        def _match(item: TradingSignal) -> bool:
            if item.user_id != user_id:
                return False
            if strategy_id is not None and item.strategy_id != strategy_id:
                return False
            if symbol is not None and item.symbol != symbol:
                return False
            if status is not None and item.status != status:
                return False
            if keyword_lower is None:
                return True
            return keyword_lower in item.symbol.lower() or keyword_lower in item.strategy_id.lower()

        return [item for item in self._signals.values() if _match(item)]

    def save_execution(self, execution: ExecutionRecord) -> None:
        self._executions[execution.id] = execution

    def list_executions(
        self,
        *,
        user_id: str,
        signal_id: str | None = None,
        status: str | None = None,
    ) -> list[ExecutionRecord]:
        return [
            item
            for item in self._executions.values()
            if item.user_id == user_id
            and (signal_id is None or item.signal_id == signal_id)
            and (status is None or item.status == status)
        ]

    def delete_signals_by_user(self, *, user_id: str) -> int:
        target_ids = [item.id for item in self._signals.values() if item.user_id == user_id]
        for signal_id in target_ids:
            del self._signals[signal_id]
        return len(target_ids)

    def delete_expired_signals_by_user(self, *, user_id: str) -> int:
        target_ids = [
            item.id
            for item in self._signals.values()
            if item.user_id == user_id and item.status == "expired"
        ]
        for signal_id in target_ids:
            del self._signals[signal_id]
        return len(target_ids)

    def delete_all_signals(self) -> int:
        count = len(self._signals)
        self._signals.clear()
        return count

    def get_batch_record(
        self,
        *,
        user_id: str,
        action: str,
        idempotency_key: str,
    ) -> tuple[str, dict] | None:
        return self._batch_records.get((user_id, action, idempotency_key))

    def save_batch_record(
        self,
        *,
        user_id: str,
        action: str,
        idempotency_key: str,
        fingerprint: str,
        result: dict,
    ) -> None:
        self._batch_records[(user_id, action, idempotency_key)] = (fingerprint, dict(result))
