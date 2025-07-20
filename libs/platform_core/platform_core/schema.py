"""CamelCase 序列化基类。

对外 API 字段统一 camelCase；内部模型字段保持 snake_case。
"""
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """将 snake_case 转换为 camelCase。"""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """所有对外 API 模型的基类，自动将字段序列化为 camelCase。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
