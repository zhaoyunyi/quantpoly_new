"""统一 API 响应信封。

提供 success_response / error_response / paged_response 三种标准响应格式。
"""
from typing import Any


def success_response(
    data: Any = None,
    message: str = "ok",
) -> dict:
    """构建成功响应。"""
    payload: dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    return payload


def error_response(
    code: str,
    message: str,
) -> dict:
    """构建错误响应。"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def paged_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "ok",
) -> dict:
    """构建分页响应。"""
    return {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    }
