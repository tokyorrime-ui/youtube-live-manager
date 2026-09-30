"""Console entry point."""

from __future__ import annotations

from .bot import LiveBot
from .config import load_settings
from .system import allow_sleep, prevent_sleep


def main() -> int:
    settings = load_settings()
    prevent_sleep()
    try:
        bot = LiveBot(settings)
        bot.run_forever()
    except KeyboardInterrupt:
        print("\n🛑 봇 종료")
    finally:
        allow_sleep()
    return 0
