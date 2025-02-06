"""
Simple utility functions to get typed environment variables with default values.

Usage:

```python
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
    """Parse environment variable as string with default value."""
    env_val = os.getenv(name) or str(default)
    return env_val


def env_int(name: str, default: int) -> int:
    """Parse environment variable as int with default value."""
    try:
        return int(env_string(name, cast(str, default)))
    except:
        return default


def env_float(name: str, default: float) -> float:
    """Parse environment variable as float with default value."""
    try:
        return float(env_string(name, cast(str, default)))
    except:
        return default


def env_bool(name: str, default: bool) -> bool:
    """Parse environment variable as bool with default value."""
    value = env_string(name, cast(str, default)).lower()
    if value in ("true", "1"):
        return True
    else:
        return False
