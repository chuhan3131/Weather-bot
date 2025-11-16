from . import common
from . import inline


routers = [common.rt, inline.rt]

__all__ = [
    "common",
    "inline",
    "routers",
]
