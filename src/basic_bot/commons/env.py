"""
Simple utility functions to get typed environment variables with default values.

Usage:
```
from basic_bot.commons import env

MY_INT = env.env_int("MY_INT", 5800)
MY_STRING = env.env_string("MY_STRING", "default")
MY_FLOAT = env.env_float("MY_FLOAT", 3.14)
MY_BOOL = env.env_bool("MY_BOOL", True)
```

"""

import os
from typing import cast


def env_string(name: str, default: str) -> str:
    env_val = os.getenv(name) or str(default)
    return env_val


def env_int(name: str, default: int) -> int:
    try:
        return int(env_string(name, cast(str, default)))
    except:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(env_string(name, cast(str, default)))
    except:
        return default


def env_bool(name: str, default: bool) -> bool:
    value = env_string(name, cast(str, default)).lower()
    if value in ("true", "1"):
        return True
    else:
        return False
