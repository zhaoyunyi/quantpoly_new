"""资源所有权（ownership）校验与最小仓库实现。

约束：
- Repository/Service 对外方法 MUST 显式接收 user_id
- 当资源不属于当前 user_id 时抛出 domain error（供路由映射为 403）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class OwnershipViolationError(PermissionError):
    """资源所有权校验失败。"""


@dataclass(frozen=True)
class OwnedResource:
    id: str
    user_id: str
    data: dict[str, Any]


class InMemoryOwnedResourceRepository:
    """最小 in-memory owned repository。"""

    def __init__(self) -> None:
        self._items: dict[str, OwnedResource] = {}

    def save(self, *, id: str, user_id: str, data: dict[str, Any]) -> None:
        self._items[id] = OwnedResource(id=id, user_id=user_id, data=data)

    def list(self, *, user_id: str) -> list[dict[str, Any]]:
        return [
            {"id": item.id, "userId": item.user_id, **item.data}
            for item in self._items.values()
            if item.user_id == user_id
        ]

    def get_by_id(self, id: str, *, user_id: str) -> dict[str, Any] | None:
        item = self._items.get(id)
        if item is None:
            return None
        if item.user_id != user_id:
            raise OwnershipViolationError("resource does not belong to current user")
        return {"id": item.id, "userId": item.user_id, **item.data}

    def delete(self, id: str, *, user_id: str) -> None:
        item = self._items.get(id)
        if item is None:
            return
        if item.user_id != user_id:
            raise OwnershipViolationError("resource does not belong to current user")
        del self._items[id]

    def update(self, id: str, *, user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        item = self._items.get(id)
        if item is None:
            return None
        if item.user_id != user_id:
            raise OwnershipViolationError("resource does not belong to current user")

        merged = {**item.data, **data}
        self._items[id] = OwnedResource(id=item.id, user_id=item.user_id, data=merged)
        return {"id": item.id, "userId": item.user_id, **merged}
