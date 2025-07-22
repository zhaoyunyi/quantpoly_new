"""Token 提取规则测试。

目标：HTTP 与 WebSocket 统一使用同一套 session token 提取逻辑。

要求（优先级）：Authorization Bearer > Cookie session_token。
"""

from user_auth.token import extract_session_token


class TestExtractSessionToken:
    """Test session token 提取优先级。"""

    def test_extract_from_cookie_when_no_bearer(self):
        token = extract_session_token(
            headers={},
            cookies={"session_token": "cookie-token"},
        )
        assert token == "cookie-token"

    def test_extract_from_bearer_over_cookie(self):
        token = extract_session_token(
            headers={"Authorization": "Bearer header-token"},
            cookies={"session_token": "cookie-token"},
        )
        assert token == "header-token"

    def test_extract_returns_none_when_missing(self):
        token = extract_session_token(headers={}, cookies={})
        assert token is None

