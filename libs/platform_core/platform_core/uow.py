"""Unit of Work 协议与基础实现。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class UnitOfWork(Protocol):
    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class NoopUnitOfWork:
    """空操作 UoW。"""

    def __enter__(self) -> "NoopUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class SnapshotUnitOfWork:
    """基于快照/恢复的 UoW 实现。"""

    def __init__(
        self,
        *,
        snapshot: Callable[[], Any],
        restore: Callable[[Any], None],
    ) -> None:
        self._snapshot = snapshot
        self._restore = restore
        self._state: Any = None
        self._committed = False

    def __enter__(self) -> "SnapshotUnitOfWork":
        self._state = self._snapshot()
        self._committed = False
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()
            return
        if not self._committed:
            self.commit()

    def commit(self) -> None:
        self._committed = True
        self._state = None

    def rollback(self) -> None:
        if self._state is None:
            return
        self._restore(self._state)
        self._state = None
        self._committed = False
