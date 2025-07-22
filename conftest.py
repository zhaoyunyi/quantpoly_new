"""pytest 全局配置。

当前仓库采用 libs/ 下多包结构；为保证在未安装各子包的情况下
也能在仓库根目录直接运行 `pytest`，这里将各库目录加入 sys.path。
"""

from __future__ import annotations

import sys
from pathlib import Path


def _add_lib_to_sys_path(lib_name: str) -> None:
    repo_root = Path(__file__).resolve().parent
    lib_root = repo_root / "libs" / lib_name
    if not lib_root.exists():
        return
    sys.path.insert(0, str(lib_root))


_add_lib_to_sys_path("platform_core")
_add_lib_to_sys_path("user_auth")
_add_lib_to_sys_path("monitoring_realtime")
