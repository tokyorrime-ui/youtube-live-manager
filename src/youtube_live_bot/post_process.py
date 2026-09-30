"""Actions executed after a live stream ends."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from .analysis import analyze_live_chat_json, build_highlight_comment
from .config import Settings
from .drive import DriveUploader
from .youtube_api import YouTubeClient
from .ytdlp import YtDlp


class PostProcessor:
    def __init__(self, settings: Settings, youtube: YouTubeClient, drive: DriveUploader, ytdlp: YtDlp):
        self.settings = settings
        self.youtube = youtube
        self.drive = drive
        self.ytdlp = ytdlp

    def start(self, video_id: str, video_title: str, log_path: Path) -> threading.Thread:
        thread = threading.Thread(
            target=self.run,
            args=(video_id, video_title, log_path),
            daemon=True,
            name=f"post-process-{video_id}",
        )
        thread.start()
        return thread

    def run(self, video_id: str, video_title: str, log_path: Path) -> None:
        chat_json_path: Path | None = None
        try:
            if log_path.exists():
                self.drive.upload_or_update(log_path)

            time.sleep(10)
            chat_json_path = self.ytdlp.collect_live_chat(video_id, video_title)
            if not chat_json_path:
                print("⚠️ 공식 live_chat JSON 다운로드 실패")
                return

            fun_results, shock_results = analyze_live_chat_json(chat_json_path)
            comment_body = build_highlight_comment(fun_results, shock_results)
            if comment_body:
                self.youtube.post_video_comment(video_id, comment_body)
                print("✅ 하이라이트 댓글 게시 완료")
        except Exception as exc:
            print(f"⚠️ 사후처리 중 오류: {exc}")
        finally:
            if chat_json_path and chat_json_path.exists():
                try:
                    chat_json_path.unlink()
                    print(f"🗑️ 분석 완료된 JSON 삭제 완료: {chat_json_path}")
                except OSError as exc:
                    print(f"⚠️ JSON 삭제 실패: {exc}")


__all__ = ["PostProcessor"]
