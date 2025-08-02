"""管理员治理审计日志。"""

from __future__ import annotations

from admin_governance.domain import AuditRecord


class InMemoryAuditLog:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, record: AuditRecord) -> None:
        self._records.append(record)

    def list_records(self) -> list[AuditRecord]:
        return list(self._records)
