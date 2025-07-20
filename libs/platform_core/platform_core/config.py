"""配置加载模块。

提供统一的配置加载机制，支持环境变量与 .env 文件，
并在不同环境（local/staging/production）下进行约束校验。
"""
import enum
import warnings
from typing import Optional

from pydantic_settings import BaseSettings


class EnvironmentType(str, enum.Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


MIN_SECRET_KEY_LENGTH = 16


class Settings(BaseSettings):
    """平台核心配置。"""

    environment: EnvironmentType = EnvironmentType.LOCAL
    secret_key: str = ""
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def validate_security(self) -> None:
        """校验安全相关配置。

        - local 环境：弱配置仅告警
        - production/staging 环境：弱配置直接拒绝启动
        """
        is_weak = not self.secret_key or len(self.secret_key) < MIN_SECRET_KEY_LENGTH

        if not is_weak:
            return

        if self.environment == EnvironmentType.LOCAL:
            warnings.warn(
                "SECRET_KEY is empty or weak in local environment. "
                "This is acceptable for development but must be fixed before deployment.",
                UserWarning,
                stacklevel=2,
            )
        else:
            raise ValueError(
                "SECRET_KEY is empty or too weak for "
                f"{self.environment.value} environment. "
                "Please set a strong SECRET_KEY (>= 16 characters)."
            )
