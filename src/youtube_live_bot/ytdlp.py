"""yt-dlp live chat collector."""

from __future__ import annotations

import glob
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

from .config import Settings


def sanitize_title(title: str | None) -> str:
    import re

    sanitized = re.sub(r"[\\/:*?\"<>|]+", "", title or "")
    return re.sub(r"\s+", "_", sanitized).strip("_")


class YtDlp:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_live_video_id(self) -> str | None:
        try:
            result = subprocess.run(
                [str(self.settings.ytdlp_path), "--print", "id", self.settings.channel_url],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            return result.stdout.strip() or None
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("[정보] 현재 라이브 방송이 없습니다.")
            return None

    def collect_live_chat(
        self,
        video_id: str,
        video_title: str | None,
        max_retry: int | None = None,
        wait_seconds: int | None = None,
    ) -> Path | None:
        max_retry = max_retry or self.settings.chat_download_retries
        wait_seconds = wait_seconds or self.settings.chat_download_retry_wait

        now_str = datetime.now().strftime("%Y-%m-%d %H_%M")
        safe_title = sanitize_title(video_title or video_id)[:120]
        output_base = self.settings.analysis_dir / f"{safe_title} {now_str} [{video_id}]"
        original_cookie_path = self.settings.cookie_source

        print(f"📥 공식 채팅 로그 다운로드 시작: {output_base}")
        print(f"🕒 첫 시도까지 {wait_seconds // 60}분 대기합니다.")
        time.sleep(self.settings.first_chat_download_wait)

        if not original_cookie_path.exists():
            print(f"⚠️ 원본 쿠키 파일이 없습니다: {original_cookie_path}")
            return None

        for attempt in range(1, max_retry + 1):
            temp_cookie_path = self.settings.analysis_dir / (
                f"cookies_run_{video_id}_{attempt}.txt"
            )
            try:
                if temp_cookie_path.exists():
                    temp_cookie_path.unlink()
                shutil.copy2(original_cookie_path, temp_cookie_path)

                command = [
                    str(self.settings.ytdlp_path),
                    "--cookies", str(temp_cookie_path),
                    "--js-runtimes", "node",
                    "--skip-download",
                    "--write-subs",
                    "--sub-langs", "live_chat",
                    "--sub-format", "json",
                    "--retries", "10",
                    "--fragment-retries", "10",
                    "--no-abort-on-error",
                    "--ignore-errors",
                    "--no-part",
                    "-o", str(output_base),
                    f"https://www.youtube.com/watch?v={video_id}",
                ]

                print(f"⏳ JSON 생성 확인 시도 {attempt}/{max_retry}")
                subprocess.run(command, check=True, timeout=300)

                candidates = [
                    Path(path)
                    for path in glob.glob(str(output_base) + "*.live_chat.json")
                    if Path(path).is_file()
                ]
                if candidates:
                    candidates.sort(
                        key=lambda path: (
                            0 if path.name.endswith(".live_chat.json") else 1,
                            len(str(path)),
                        )
                    )
                    return candidates[0]
            except subprocess.TimeoutExpired:
                print("⚠️ yt-dlp 실행이 너무 오래 걸렸습니다. 다음 재시도 때 다시 확인합니다.")
            except Exception as exc:
                print(f"⚠️ 다운로드 시도 실패: {exc}")
            finally:
                temp_cookie_path.unlink(missing_ok=True)

            if attempt < max_retry:
                print(f"🕒 {wait_seconds // 60}분 후 다시 시도합니다.")
                time.sleep(wait_seconds)

        return None
