"""Persistent smoke/food stack state."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

PAIR_META = {
    "smoke": {"positive": "금연", "negative": "흡연"},
    "food": {"positive": "먹지마", "negative": "먹어"},
}
LABEL_TO_GROUP = {
    "금연": "smoke",
    "흡연": "smoke",
    "먹지마": "food",
    "먹어": "food",
}


class StackManager:
    def __init__(self, path: Path, state_version: int = 1):
        self.path = path
        self.state_version = state_version

    def _now(self) -> datetime:
        return datetime.now()

    def _empty_state(self) -> dict:
        return {
            "version": self.state_version,
            "pairs": {"smoke": None, "food": None},
            "smoke_time_base": None,
            "food_time_base": None,
        }

    def load(self) -> dict:
        if not self.path.exists():
            return self._empty_state()
        try:
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return self._empty_state()
            data = json.loads(raw)
            if not isinstance(data, dict) or "pairs" not in data:
                return self._empty_state()
            state = self._empty_state()
            state["version"] = data.get("version", self.state_version)
            state["pairs"]["smoke"] = data.get("pairs", {}).get("smoke")
            state["pairs"]["food"] = data.get("pairs", {}).get("food")
            old_time = data.get("time_base")
            state["smoke_time_base"] = data.get("smoke_time_base", old_time)
            state["food_time_base"] = data.get("food_time_base", old_time)
            return state
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return self._empty_state()

    def save(self, state: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _dt_to_str(value: datetime) -> str:
        return value.isoformat(timespec="seconds")

    @staticmethod
    def _str_to_dt(value: str) -> datetime:
        return datetime.fromisoformat(value)

    def _elapsed_hours_from_base(self, state: dict, group: str, now: datetime) -> int:
        key = "smoke_time_base" if group == "smoke" else "food_time_base"
        if not state.get(key):
            return 0
        base = self._str_to_dt(state[key])
        return max(0, int((now - base).total_seconds() // 3600))

    @staticmethod
    def _effective_entry(entry: dict | None, elapsed_hours: int) -> dict | None:
        if not entry:
            return None
        return {"side": entry["side"], "value": max(0, int(entry["value"]) - elapsed_hours)}

    @staticmethod
    def _signed_value(entry: dict | None, group: str) -> int:
        if not entry:
            return 0
        if entry["side"] == PAIR_META[group]["positive"]:
            return int(entry["value"])
        if entry["side"] == PAIR_META[group]["negative"]:
            return -int(entry["value"])
        return 0

    @staticmethod
    def _from_signed_value(group: str, signed_value: int, elapsed_hours: int, fallback_side: str | None) -> dict:
        if signed_value > 0:
            return {"side": PAIR_META[group]["positive"], "value": signed_value + elapsed_hours}
        if signed_value < 0:
            return {"side": PAIR_META[group]["negative"], "value": abs(signed_value) + elapsed_hours}
        return {"side": fallback_side or PAIR_META[group]["positive"], "value": elapsed_hours}

    def update(self, label: str, number: int, mode: str) -> None:
        now = self._now()
        state = self.load()
        group = LABEL_TO_GROUP[label]
        elapsed_hours = self._elapsed_hours_from_base(state, group, now)
        entry = self._effective_entry(state["pairs"].get(group), elapsed_hours)
        current_signed = self._signed_value(entry, group)

        if mode == "set":
            state["pairs"][group] = {"side": label, "value": int(number) + elapsed_hours}
        else:
            if mode == "add":
                delta = int(number) if label in ("금연", "먹지마") else -int(number)
            elif mode == "delete":
                delta = -int(number) if label in ("금연", "먹지마") else int(number)
            else:
                raise ValueError(f"Unsupported stack mode: {mode}")
            new_signed = current_signed + delta
            fallback_side = entry["side"] if entry else PAIR_META[group]["positive"]
            if current_signed == 0 and new_signed != 0:
                state["smoke_time_base" if group == "smoke" else "food_time_base"] = self._dt_to_str(now)
                elapsed_hours = 0
            state["pairs"][group] = self._from_signed_value(
                group, new_signed, elapsed_hours, fallback_side
            )

        time_key = "smoke_time_base" if group == "smoke" else "food_time_base"
        if mode == "set" and int(number) > 0:
            current = self._effective_entry(state["pairs"].get(group), elapsed_hours)
            if current is None or current["value"] == 0:
                state[time_key] = self._dt_to_str(now)

        self.save(state)

    def set_time_base(self, time_text: str | None = None) -> None:
        now = self._now()
        state = self.load()
        for group in ("smoke", "food"):
            elapsed_hours = self._elapsed_hours_from_base(state, group, now)
            entry = self._effective_entry(state["pairs"].get(group), elapsed_hours)
            if entry:
                state["pairs"][group] = entry

        if time_text:
            hour, minute = map(int, time_text.split(":"))
            base = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            base = now

        base_str = self._dt_to_str(base)
        state["smoke_time_base"] = base_str
        state["food_time_base"] = base_str
        self.save(state)

    def delete_time_base(self) -> None:
        state = self.load()
        state["smoke_time_base"] = None
        state["food_time_base"] = None
        self.save(state)

    def format_time_base(self, group: str) -> str | None:
        now = self._now()
        state = self.load()
        key = "smoke_time_base" if group == "smoke" else "food_time_base"
        if not state.get(key):
            return None
        base = self._str_to_dt(state[key])
        elapsed_hours = max(0, int((now - base).total_seconds() // 3600))
        display_time = base + timedelta(hours=elapsed_hours)
        return display_time.strftime("%H:%M")

    def format_text(self) -> str:
        now = self._now()
        state = self.load()
        parts: list[str] = []
        for group in ("smoke", "food"):
            elapsed = self._elapsed_hours_from_base(state, group, now)
            entry = self._effective_entry(state["pairs"].get(group), elapsed)
            if not entry:
                continue
            label = entry["side"]
            value = entry["value"]
            time_base = self.format_time_base(group)
            parts.append(f"{label} {value} ({time_base})" if time_base else f"{label} {value}")

        return "🚬 " + " / ".join(parts) if parts else ""
