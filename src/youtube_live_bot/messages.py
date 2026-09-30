"""Chat reply configuration loaded from a local JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_REPLIES: dict[str, Any] = {
    "hourly_message": "▶▷후원자비하,풍막발언은 채금,블랙의 사유가될수있습니다⚠️",
    "mission_message": "📢 미션 편하게 주세요",
    "donation_message": "후원 안내 문구를 config/auto_replies.json에 설정하세요.",
    "commands": {
        "!시그": [],
        "!메뉴": ["메뉴 내용을 config/auto_replies.json에 설정하세요."],
    },
}


class MessageStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULT_REPLIES)
        try:
            with self.path.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"⚠️ 자동응답 설정 로드 실패: {exc}")
            return dict(DEFAULT_REPLIES)

        if not isinstance(loaded, dict):
            return dict(DEFAULT_REPLIES)

        merged = dict(DEFAULT_REPLIES)
        merged.update(loaded)
        if not isinstance(merged.get("commands"), dict):
            merged["commands"] = dict(DEFAULT_REPLIES["commands"])
        return merged

    @property
    def hourly_message(self) -> str:
        return str(self.data.get("hourly_message", ""))

    @property
    def mission_message(self) -> str:
        return str(self.data.get("mission_message", ""))

    @property
    def donation_message(self) -> str:
        return str(self.data.get("donation_message", ""))

    @property
    def commands(self) -> dict[str, Any]:
        return self.data.get("commands", {})
