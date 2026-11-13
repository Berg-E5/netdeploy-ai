"""配置读取 —— 环境变量名带向后兼容。

本项目的前缀是 VPSDEPLOY_*。上游用的是 NETDEPLOY_*，很多人（包括早期版本的
自己）已经按上游的名字写好了 .env 和 compose 配置。直接改名会让那些配置
全部失效，所以这里统一走 env()：

    先读 VPSDEPLOY_xxx，没有再回退到 NETDEPLOY_xxx。

新写的配置、文档和示例一律用 VPSDEPLOY_*；老配置继续可用，只是不再推荐。
"""
from __future__ import annotations

import os

PREFIX = "VPSDEPLOY_"
LEGACY_PREFIX = "NETDEPLOY_"


def env(name: str, default: str = "") -> str:
    """读环境变量：新前缀优先，回退到旧前缀。

    name 传不带前缀的名字，例如 env("ADMIN_TOKEN")。
    """
    value = os.environ.get(PREFIX + name)
    if value is not None:
        return value
    legacy = os.environ.get(LEGACY_PREFIX + name)
    if legacy is not None:
        return legacy
    return default


def env_flag(name: str, default: str = "0") -> bool:
    return env(name, default) == "1"


def env_int(name: str, default: int = 0) -> int:
    raw = env(name, "")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default
