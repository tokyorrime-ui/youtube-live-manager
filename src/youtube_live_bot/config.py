"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name, "").strip()
    return Path(value).expanduser() if value else default


def _int_from_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer: {value!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the bot."""

    channel_url: str
    youtube_token_path: Path
    drive_token_path: Path
    drive_folder_id: str
    ytdlp_path: Path
    cookie_source: Path
    cookie_live: Path | None

    data_dir: Path
    log_dir: Path
    notice_dir: Path
    state_dir: Path
    analysis_dir: Path
    auto_replies_path: Path

    command_cooldown: int
    hourly_interval: int
    mission_interval: int
    max_error_count: int
    end_check_interval: int
    stack_command_cooldown: int
    member_command_cooldown: int
    member_max_count: int
    first_chat_download_wait: int
    chat_download_retries: int
    chat_download_retry_wait: int

    stack_state_version: int = 1

    @property
    def notice_file(self) -> Path:
        return self.notice_dir / "notice_content.txt"

    @property
    def smoke_state_file(self) -> Path:
        return self.notice_dir / "smoke_content.txt"

    @property
    def hungry_file(self) -> Path:
        return self.notice_dir / "hungry_content.txt"

    @property
    def money_file(self) -> Path:
        return self.notice_dir / "money_content.txt"

    @property
    def member_file(self) -> Path:
        return self.state_dir / "members.json"


def load_settings() -> Settings:
    data_dir = _path_from_env("BOT_DATA_DIR", PROJECT_ROOT / "data")

    settings = Settings(
        channel_url=os.getenv(
            "YOUTUBE_CHANNEL_URL",
            "https://www.youtube.com/@your_channel/live",
        ),
        youtube_token_path=_path_from_env(
            "YOUTUBE_TOKEN_PATH", PROJECT_ROOT / "credentials" / "youtube_token.json"
        ),
        drive_token_path=_path_from_env(
            "GOOGLE_DRIVE_TOKEN_PATH", PROJECT_ROOT / "credentials" / "drive_token.json"
        ),
        drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),
        ytdlp_path=_path_from_env("YTDLP_PATH", Path("yt-dlp.exe")),
        cookie_source=_path_from_env("COOKIE_SOURCE", PROJECT_ROOT / "credentials" / "cookies.txt"),
        cookie_live=_path_from_env("COOKIE_LIVE", PROJECT_ROOT / "credentials" / "cookies_live.txt"),
        data_dir=data_dir,
        log_dir=data_dir / "live_logs",
        notice_dir=data_dir / "notices",
        state_dir=data_dir / "state",
        analysis_dir=data_dir / "analysis",
        auto_replies_path=_path_from_env(
            "AUTO_REPLIES_PATH", PROJECT_ROOT / "config" / "auto_replies.json"
        ),
        command_cooldown=_int_from_env("COMMAND_COOLDOWN", 30),
        hourly_interval=_int_from_env("HOURLY_INTERVAL", 1500),
        mission_interval=_int_from_env("MISSION_INTERVAL", 2700),
        max_error_count=_int_from_env("MAX_ERROR_COUNT", 3),
        end_check_interval=_int_from_env("END_CHECK_INTERVAL", 30),
        stack_command_cooldown=_int_from_env("STACK_COMMAND_COOLDOWN", 7),
        member_command_cooldown=_int_from_env("MEMBER_COMMAND_COOLDOWN", 7),
        member_max_count=_int_from_env("MEMBER_MAX_COUNT", 10),
        first_chat_download_wait=_int_from_env("FIRST_CHAT_DOWNLOAD_WAIT", 600),
        chat_download_retries=_int_from_env("CHAT_DOWNLOAD_RETRIES", 30),
        chat_download_retry_wait=_int_from_env("CHAT_DOWNLOAD_RETRY_WAIT", 600),
    )

    for path in (
        settings.data_dir,
        settings.log_dir,
        settings.notice_dir,
        settings.state_dir,
        settings.analysis_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)

    return settings
