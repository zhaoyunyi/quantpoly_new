"""日志脱敏模块。

提供统一的敏感信息脱敏策略，覆盖：token、cookie、密码、API key。
"""
import logging
import re

# 敏感值前缀保留长度
_PREFIX_LENGTH = 4
_MASK = "***"

# 匹配模式：Bearer token
_BEARER_RE = re.compile(r"(Bearer\s+)(\S{8,})", re.IGNORECASE)

# 匹配模式：key=value 形式的敏感字段（词边界防止误匹配）
_KV_SENSITIVE_RE = re.compile(
    r"(\b(?:password|api_key|api[-_]?secret|token|cookie|secret_key)"
    r"\s*[=:]\s*)"
    r"(\S+)",
    re.IGNORECASE,
)


def _mask_value(value: str) -> str:
    """保留前缀 + 掩码。"""
    if len(value) <= _PREFIX_LENGTH:
        return _MASK
    return value[:_PREFIX_LENGTH] + _MASK


def mask_sensitive(text: str) -> str:
    """对文本中的敏感信息进行脱敏。

    规则：
    - Bearer token：保留前 4 字符 + ***
    - password/api_key/token/cookie/secret_key 等 key=value：保留前 4 字符 + ***
    """
    # 先处理 Bearer token
    result = _BEARER_RE.sub(
        lambda m: m.group(1) + _mask_value(m.group(2)),
        text,
    )
    # 再处理 key=value 形式
    result = _KV_SENSITIVE_RE.sub(
        lambda m: m.group(1) + _mask_value(m.group(2)),
        result,
    )
    return result


class SensitiveFilter(logging.Filter):
    """日志过滤器：自动脱敏日志消息中的敏感信息。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # 参数化日志场景（record.msg + record.args）需要先格式化成最终字符串，
            # 否则仅替换 record.msg 会导致 formatter 二次格式化时报错或泄漏 args。
            try:
                message = record.getMessage()
            except Exception:
                # 兜底：确保 filter 不抛异常，并避免 formatter 再次尝试格式化。
                record.msg = mask_sensitive(record.msg)
                record.args = ()
                return True

            record.msg = mask_sensitive(message)
            record.args = ()
        return True
