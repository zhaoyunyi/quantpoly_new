"""signal_execution in-memory 仓储。"""

from __future__ import annotations

from signal_execution.domain import ExecutionRecord, TradingSignal


class InMemorySignalRepository:
    def __init__(self) -> None:
        self._signals: dict[str, TradingSignal] = {}
        self._executions: dict[str, ExecutionRecord] = {}

    def save_signal(self, signal: TradingSignal) -> None:
        self._signals[signal.id] = signal

    def get_signal(self, *, signal_id: str, user_id: str) -> TradingSignal | None:
        item = self._signals.get(signal_id)
        if item is None or item.user_id != user_id:
            return None
        return item

    def list_signals(self, *, user_id: str, keyword: str | None = None) -> list[TradingSignal]:
        keyword_lower = keyword.lower() if keyword else None
        signals = [item for item in self._signals.values() if item.user_id == user_id]
        if keyword_lower is None:
            return signals

        return [
            item
            for item in signals
            if keyword_lower in item.symbol.lower() or keyword_lower in item.strategy_id.lower()
        ]

    def save_execution(self, execution: ExecutionRecord) -> None:
        self._executions[execution.id] = execution

    def list_executions(self, *, user_id: str) -> list[ExecutionRecord]:
        return [item for item in self._executions.values() if item.user_id == user_id]

    def delete_signals_by_user(self, *, user_id: str) -> int:
        target_ids = [item.id for item in self._signals.values() if item.user_id == user_id]
        for signal_id in target_ids:
            del self._signals[signal_id]
        return len(target_ids)

    def delete_all_signals(self) -> int:
        count = len(self._signals)
        self._signals.clear()
        return count
