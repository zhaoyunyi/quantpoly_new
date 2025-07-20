"""响应信封与 camelCase 序列化测试 — Red 阶段。

BDD Scenarios from spec:
- success_response 返回一致结构
- error_response 返回一致结构
- 响应字段自动序列化为 camelCase
"""
import pytest

from platform_core.response import (
    success_response,
    error_response,
    paged_response,
)
from platform_core.schema import CamelModel


class TestSuccessResponse:
    """Test统一成功响应。"""

    def test_success_response_structure(self):
        result = success_response(data={"id": 1}, message="ok")
        assert result["success"] is True
        assert result["message"] == "ok"
        assert result["data"] == {"id": 1}

    def test_success_response_default_message(self):
        result = success_response(data={"id": 1})
        assert result["success"] is True
        assert "message" in result


class TestErrorResponse:
    """Test统一错误响应。"""

    def test_error_response_structure(self):
        result = error_response(code="VALIDATION_ERROR", message="invalid input")
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "invalid input"

    def test_error_response_no_data_field(self):
        result = error_response(code="NOT_FOUND", message="not found")
        assert "data" not in result
