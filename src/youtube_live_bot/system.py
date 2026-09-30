"""Operating-system helpers."""

from __future__ import annotations

import ctypes
import os


_EXECUTION_STATE = 0x80000001 | 0x00000040
_CONTINUOUS = 0x80000000


def prevent_sleep() -> None:
    if os.name == "nt":
        ctypes.windll.kernel32.SetThreadExecutionState(_EXECUTION_STATE)


def allow_sleep() -> None:
    if os.name == "nt":
        ctypes.windll.kernel32.SetThreadExecutionState(_CONTINUOUS)
