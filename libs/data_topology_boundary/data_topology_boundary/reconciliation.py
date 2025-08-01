"""迁移前后数据一致性对账。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ReconciliationReport:
    consistent: bool
    missing_ids: list[str]
    extra_ids: list[str]
    mismatch_count: int
    before_count: int
    after_count: int


def reconcile_by_key(
    *,
    before_rows: list[dict[str, Any]],
    after_rows: list[dict[str, Any]],
    key: str,
) -> ReconciliationReport:
    before_map = {str(item[key]): item for item in before_rows if key in item}
    after_map = {str(item[key]): item for item in after_rows if key in item}

    before_ids = set(before_map.keys())
    after_ids = set(after_map.keys())

    missing_ids = sorted(before_ids - after_ids)
    extra_ids = sorted(after_ids - before_ids)

    mismatch_count = 0
    for item_id in before_ids & after_ids:
        if before_map[item_id] != after_map[item_id]:
            mismatch_count += 1

    return ReconciliationReport(
        consistent=(not missing_ids and not extra_ids and mismatch_count == 0),
        missing_ids=missing_ids,
        extra_ids=extra_ids,
        mismatch_count=mismatch_count,
        before_count=len(before_rows),
        after_count=len(after_rows),
    )
