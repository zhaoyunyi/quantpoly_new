"""跨上下文回调/适配器契约校验。

背景：在 break update 的治理阶段，跨上下文交互（ACL/OHS、回调、适配器）
必须显式接收 `user_id` 与资源标识，并以关键字参数调用。

本模块提供最小的签名校验工具，用于在 service 初始化时 fail-fast，
避免在运行时通过 try/except TypeError 静默回退到 legacy 签名。
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence


def require_explicit_keyword_parameters(
    callback: Callable[..., object] | None,
    *,
    required: Sequence[str],
    callback_name: str,
) -> None:
    """要求 callback 显式声明 required 参数，且可用关键字传参。

    - 不允许仅依赖 `**kwargs` 隐式接收（避免契约漂移）。
    - 仅做签名层校验，不执行回调。
    """

    if callback is None:
        return

    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError) as exc:  # pragma: no cover
        raise TypeError(f"{callback_name} 必须是可获取签名的 Python callable") from exc

    missing: list[str] = []
    positional_only: list[str] = []
    for name in required:
        param = signature.parameters.get(name)
        if param is None:
            missing.append(name)
            continue
        if param.kind is inspect.Parameter.POSITIONAL_ONLY:
            positional_only.append(name)

    if missing or positional_only:
        details: list[str] = []
        if missing:
            details.append(f"missing={missing}")
        if positional_only:
            details.append(f"positional_only={positional_only}")
        rendered = ", ".join(details)
        raise TypeError(
            f"{callback_name} 回调签名不满足要求（{rendered}）。"
            f"必须显式声明并支持关键字参数：{list(required)}；"
            f"当前签名为：{signature}"
        )

