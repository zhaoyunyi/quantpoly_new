"""配置加载模块测试 — Red 阶段。

BDD Scenarios from spec:
- local 环境允许弱配置但给出告警
- production 环境拒绝弱配置
"""
import warnings

import pytest

from platform_core.config import Settings, EnvironmentType


class TestSettings:
    """Test平台核心配置加载。"""

    # ── Scenario: 默认环境为 local ──

    def test_default_environment_is_local(self, monkeypatch):
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)
        settings = Settings(_env_file=None)
        assert settings.environment == EnvironmentType.LOCAL

    # ── Scenario: 从环境变量加载配置 ──

    def test_load_from_env_var(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "a-very-strong-secret-key-1234567890")
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings = Settings(_env_file=None)
        assert settings.secret_key == "a-very-strong-secret-key-1234567890"
        assert settings.environment == EnvironmentType.PRODUCTION

    # ── Scenario: local 环境允许弱配置但给出告警 ──

    def test_local_weak_secret_key_warns(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("SECRET_KEY", "")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            settings = Settings(_env_file=None)
            settings.validate_security()
            assert any("SECRET_KEY" in str(warning.message) for warning in w)

    def test_local_weak_secret_key_still_starts(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("SECRET_KEY", "")
        settings = Settings(_env_file=None)
        # 不应抛出异常
        settings.validate_security()

    # ── Scenario: production 环境拒绝弱配置 ──

    def test_production_empty_secret_key_raises(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "")
        settings = Settings(_env_file=None)
        with pytest.raises(ValueError, match="SECRET_KEY"):
            settings.validate_security()

    def test_production_weak_secret_key_raises(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "short")
        settings = Settings(_env_file=None)
        with pytest.raises(ValueError, match="SECRET_KEY"):
            settings.validate_security()

    # ── Scenario: 错误信息不应包含敏感值 ──

    def test_error_message_does_not_leak_secret(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "short")
        settings = Settings(_env_file=None)
        with pytest.raises(ValueError) as exc_info:
            settings.validate_security()
        assert "short" not in str(exc_info.value)
