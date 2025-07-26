"""FastAPI 层的 ownership 错误映射。"""

from __future__ import annotations

from fastapi import HTTPException


def raise_ownership_forbidden(detail: str = "Forbidden") -> None:
    raise HTTPException(status_code=403, detail=detail)

