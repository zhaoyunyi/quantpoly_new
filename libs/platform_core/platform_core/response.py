"""统一 API 响应信封。

提供 success_response / error_response / paged_response 三种标准响应格式。
"""
from typing import Any, Optional


def success_response(
    data: Any = None,
    message: str = "ok",
) -> dict:
    """构建成功响应。"""
    return {
        "success": True,
        "message": message,
        "data": data,
    }


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
) -> dict:
    """构建分页响应。"""
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    }
