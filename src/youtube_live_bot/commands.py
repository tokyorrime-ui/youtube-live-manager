"""Live chat command handling."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .members import MemberManager
from .messages import MessageStore
from .stack import StackManager


@dataclass(frozen=True)
class CommandResult:
    replies: list[str] | None = None
    refresh_stack: bool = False
    refresh_members: bool = False
    command_name: str | None = None


class CommandHandler:
    def __init__(self, settings: Settings, messages: MessageStore, stack: StackManager, members: MemberManager):
        self.settings = settings
        self.messages = messages
        self.stack = stack
        self.members = members
        self.last_command_time: dict[str, float] = {}
        self.last_stack_command_time = 0.0
        self.last_member_command_time = 0.0

    def can_send(self, command: str) -> bool:
        now = time.time()
        last = self.last_command_time.get(command, 0.0)
        if now - last > self.settings.command_cooldown:
            self.last_command_time[command] = now
            return True
        return False

    def _can_use_stack(self) -> bool:
        now = time.time()
        if now - self.last_stack_command_time < self.settings.stack_command_cooldown:
            return False
        self.last_stack_command_time = now
        return True

    def _can_use_member_mutation(self) -> bool:
        now = time.time()
        if now - self.last_member_command_time < self.settings.member_command_cooldown:
            return False
        self.last_member_command_time = now
        return True

    def handle(self, text: str, is_moderator: bool, actual_start_time: datetime | None) -> CommandResult:
        text = text.strip()
        if not text:
            return CommandResult()

        stack_set = re.match(r"^!스택\s+설정\s+(금연|흡연|먹지마|먹어)(\d+)\s*$", text)
        stack_add = re.match(r"^!스택\s+추가\s+(금연|흡연|먹지마|먹어)(\d+)\s*$", text)
        stack_del = re.match(r"^!스택\s+삭제\s+(금연|흡연|먹지마|먹어)(\d+)\s*$", text)
        stack_time = re.match(r"^!스택\s+시간(?:\s+(\d{1,2}:\d{2}))?\s*$", text)
        member_add = re.match(r"^!멤버\s+추가\s+(\S+?)(\d+)\s*$", text)
        member_del = re.match(r"^!멤버\s+삭제\s+(\S+?)(\d+)\s*$", text)
        member_remove = re.match(r"^!멤버\s+제거\s+(\S+)\s*$", text)

        if is_moderator and stack_set:
            if not self._can_use_stack():
                return CommandResult()
            self.stack.update(stack_set.group(1), int(stack_set.group(2)), "set")
            return CommandResult(refresh_stack=True)

        if is_moderator and stack_add:
            if not self._can_use_stack():
                return CommandResult()
            self.stack.update(stack_add.group(1), int(stack_add.group(2)), "add")
            return CommandResult(refresh_stack=True)

        if is_moderator and stack_del:
            if not self._can_use_stack():
                return CommandResult()
            self.stack.update(stack_del.group(1), int(stack_del.group(2)), "delete")
            return CommandResult(refresh_stack=True)

        if is_moderator and stack_time:
            if not self._can_use_stack():
                return CommandResult()
            self.stack.set_time_base(stack_time.group(1))
            return CommandResult(refresh_stack=True)

        if is_moderator and text == "!스택 삭제 시간":
            if not self._can_use_stack():
                return CommandResult()
            self.stack.delete_time_base()
            return CommandResult(refresh_stack=True)

        if is_moderator and member_add:
            if not self._can_use_member_mutation():
                return CommandResult()
            success, _result = self.members.add(member_add.group(1), int(member_add.group(2)))
            return CommandResult(refresh_members=True) if success else CommandResult()

        if is_moderator and member_del:
            if not self._can_use_member_mutation():
                return CommandResult()
            if self.members.subtract(member_del.group(1), int(member_del.group(2))):
                return CommandResult(refresh_members=True)
            return CommandResult()

        if is_moderator and member_remove:
            if not self._can_use_member_mutation():
                return CommandResult()
            if self.members.remove(member_remove.group(1)):
                return CommandResult(refresh_members=True)
            return CommandResult()

        if text == "!멤버" and self.can_send("!멤버"):
            value = self.members.format_text()
            return CommandResult([value] if value else [], command_name="!멤버")

        if text == "!스택" and self.can_send("!스택"):
            value = self.stack.format_text()
            return CommandResult([value] if value else [], command_name="!스택")

        if text == "!uptime" and self.can_send("!uptime"):
            if not actual_start_time:
                return CommandResult(["⚠️ 방송 시작 시간을 확인할 수 없습니다."], command_name="!uptime")
            elapsed = int((datetime.now(timezone.utc) - actual_start_time).total_seconds())
            limit = (11 * 3600) + (55 * 60)
            remaining = limit - elapsed
            if remaining >= 0:
                hours, rem = divmod(remaining, 3600)
                minutes, seconds = divmod(rem, 60)
                return CommandResult([f"리방까지 남은시간 {hours}시간 {minutes}분 {seconds}초 입니다."], command_name="!uptime")
            over = abs(remaining)
            hours, rem = divmod(over, 3600)
            minutes, seconds = divmod(rem, 60)
            return CommandResult([f"리방 시간이 {hours}시간 {minutes}분 {seconds}초 초과되었습니다"], command_name="!uptime")

        command_replies = self.messages.commands.get(text)
        if command_replies is not None and self.can_send(text):
            if isinstance(command_replies, list):
                return CommandResult([str(reply) for reply in command_replies], command_name=text)
            return CommandResult([str(command_replies)], command_name=text)

        return CommandResult()


class NoticeStore:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _write(self, path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def _read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def handle_registration(self, text: str, is_moderator: bool) -> bool:
        if not is_moderator:
            return False
        if text.startswith("!알리미 등록"):
            self._write(self.settings.notice_file, text.replace("!알리미 등록", "", 1).strip())
            return True
        if text.startswith("!위치 등록"):
            self._write(self.settings.hungry_file, text.replace("!위치 등록", "", 1).strip())
            return True
        if text.startswith("!용돈 등록"):
            self._write(self.settings.money_file, text.replace("!용돈 등록", "", 1).strip())
            return True
        return False

    def handle_lookup(self, text: str) -> str | None:
        mapping = {
            "!공지": (self.settings.notice_file, "📢"),
            "!위치": (self.settings.hungry_file, "🌏"),
            "!용돈": (self.settings.money_file, "💰"),
        }
        path_info = mapping.get(text)
        if not path_info:
            return None
        path, prefix = path_info
        value = self._read(path)
        return f"{prefix} {value}" if value else None
