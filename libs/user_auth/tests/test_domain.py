"""User 聚合根与 Credential 值对象测试 — Red 阶段。

BDD Scenarios:
- 用户注册成功
- 弱口令注册被拒绝
- 密码验证正确/错误
- 错误信息不泄漏安全策略细节
"""
import pytest

from user_auth.domain import User, Credential, PasswordTooWeakError


class TestCredential:
    """Test密码凭证值对象。"""

    def test_create_credential_hashes_password(self):
        cred = Credential.create("StrongPass123!")
        assert cred.hashed_password != "StrongPass123!"
        assert cred.hashed_password.startswith("$2b$")

    def test_verify_correct_password(self):
        cred = Credential.create("StrongPass123!")
        assert cred.verify("StrongPass123!") is True

    def test_verify_wrong_password(self):
        cred = Credential.create("StrongPass123!")
        assert cred.verify("WrongPassword") is False


class TestUser:
    """Test用户聚合根。"""

    def test_register_user_success(self):
        user = User.register(
            email="test@example.com",
            password="StrongPass123!",
        )
        assert user.email == "test@example.com"
        assert user.id is not None
        assert user.is_active is True

    def test_register_weak_password_rejected(self):
        with pytest.raises(PasswordTooWeakError):
            User.register(email="test@example.com", password="password")

    def test_register_short_password_rejected(self):
        with pytest.raises(PasswordTooWeakError):
            User.register(email="test@example.com", password="Ab1!")

    def test_register_no_digit_rejected(self):
        with pytest.raises(PasswordTooWeakError):
            User.register(email="test@example.com", password="StrongPassNoDigit!")

    def test_error_message_no_policy_leak(self):
        """错误信息不泄漏安全策略细节（避免被枚举）。"""
        with pytest.raises(PasswordTooWeakError) as exc_info:
            User.register(email="test@example.com", password="weak")
        msg = str(exc_info.value)
        assert "8" not in msg  # 不泄漏最小长度
        assert "digit" not in msg.lower()  # 不泄漏具体规则

    def test_authenticate_success(self):
        user = User.register(
            email="test@example.com",
            password="StrongPass123!",
        )
        assert user.authenticate("StrongPass123!") is True

    def test_authenticate_failure(self):
        user = User.register(
            email="test@example.com",
            password="StrongPass123!",
        )
        assert user.authenticate("WrongPassword") is False

    def test_disable_then_enable_updates_status(self):
        user = User.register(
            email="status@example.com",
            password="StrongPass123!",
        )

        user.disable()
        assert user.is_active is False

        user.enable()
        assert user.is_active is True
