"""QuantPoly 平台核心库。

提供统一的配置加载、API 响应信封、日志脱敏、camelCase 序列化等基础能力。
"""

from platform_core.callback_contract import require_explicit_keyword_parameters
from platform_core.uow import NoopUnitOfWork, SnapshotUnitOfWork, UnitOfWork

__all__ = [
    "require_explicit_keyword_parameters",
    "UnitOfWork",
    "NoopUnitOfWork",
    "SnapshotUnitOfWork",
]
