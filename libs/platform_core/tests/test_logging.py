"""日志脱敏模块测试 — Red 阶段。

BDD Scenarios from spec:
- 打印认证信息时不泄漏 token
- 覆盖 token / cookie / password / api_key
"""
import pytest

from platform_core.logging import SensitiveFilter, mask_sensitive


class TestMaskSensitive:
    """Test敏感信息脱敏函数。"""

    def test_mask_token(self):
        text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"
        result = mask_sensitive(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "***" in result

    def test_mask_password_field(self):
        text = 'password=SuperSecret123'
        result = mask_sensitive(text)
        assert "SuperSecret123" not in result

    def test_mask_api_key(self):
        text = 'api_key=sk-1234567890abcdef'
        result = mask_sensitive(text)
        assert "sk-1234567890abcdef" not in result

    def test_mask_cookie(self):
        text = 'cookie=session_id=abc123xyz789longvalue'
        result = mask_sensitive(text)
        assert "abc123xyz789longvalue" not in result

    def test_token_shows_prefix_and_mask(self):
        """token 只能以固定长度前缀 + 掩码形式出现。"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        text = f"Authorization: Bearer {token}"
        result = mask_sensitive(text)
        # 应保留前几个字符作为前缀
        assert result.startswith("Authorization: Bearer eyJh")
        assert "***" in result

    def test_non_sensitive_text_unchanged(self):
        text = "User logged in successfully"
        result = mask_sensitive(text)
        assert result == text

    def test_mask_json_like_context_fields(self):
        text = (
            "auth_failed ctx={'authorization': 'Bearer abcdefghijkl', "
            "'cookie': 'session_token=verysecrettoken', 'password': 'Passw0rd!'}"
        )
        result = mask_sensitive(text)
        assert "abcdefghijkl" not in result
        assert "verysecrettoken" not in result
        assert "Passw0rd!" not in result
        assert "***" in result


class TestSensitiveFilter:
    """Test日志过滤器集成。"""

    def test_filter_masks_log_record(self):
        import logging

        filt = SensitiveFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig",
            args=None,
            exc_info=None,
        )
        filt.filter(record)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in record.msg

    def test_filter_parameterized_log_record_no_error_and_masked(self):
        """参数化日志（msg + args）场景应可安全脱敏且不抛异常。"""
        import logging

        filt = SensitiveFilter()
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="token=%s",
            args=(token,),
            exc_info=None,
        )

        filt.filter(record)

        # filter 后应保证 formatter 可再次安全调用 getMessage()
        message = record.getMessage()
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in message
        assert "***" in message
