"""Persistent membership scoreboard."""

from __future__ import annotations

import json
from pathlib import Path


class MemberManager:
    def __init__(self, path: Path, max_count: int = 10):
        self.path = path
        self.max_count = max_count

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []

        result = []
        for member in data:
            if not isinstance(member, dict):
                continue
            name = str(member.get("name", "")).strip()
            try:
                value = max(0, int(member.get("value", 0)))
            except (TypeError, ValueError):
                value = 0
            if name:
                result.append({"name": name, "value": value})
        return result[: self.max_count]

    def save(self, members: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(members, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, name: str, value: int) -> tuple[bool, str]:
        members = self.load()
        name = name.strip()
        value = int(value)
        for member in members:
            if member["name"] == name:
                member["value"] = max(0, int(member["value"]) + value)
                self.save(members)
                return True, "updated"

        if len(members) >= self.max_count:
            return False, "full"
        members.append({"name": name, "value": max(0, value)})
        self.save(members)
        return True, "added"

    def subtract(self, name: str, value: int) -> bool:
        members = self.load()
        name = name.strip()
        value = int(value)
        for member in members:
            if member["name"] == name:
                member["value"] = max(0, int(member["value"]) - value)
                self.save(members)
                return True
        return False

    def remove(self, name: str) -> bool:
        members = self.load()
        new_members = [member for member in members if member["name"] != name.strip()]
        if len(new_members) == len(members):
            return False
        self.save(new_members)
        return True

    def format_text(self) -> str:
        members = self.load()
        if not members:
            return ""
        return "👤 " + " / ".join(f"{m['name']} {m['value']}" for m in members)
