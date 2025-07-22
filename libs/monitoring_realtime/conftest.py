"""monitoring_realtime 测试环境配置。

支持在 `libs/monitoring_realtime` 目录下直接运行 `pytest`。
"""

from __future__ import annotations

import sys
from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PACKAGE_ROOT))

