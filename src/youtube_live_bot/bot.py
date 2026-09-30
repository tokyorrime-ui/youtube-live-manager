"""Main live-stream monitoring loop."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path

from googleapiclient.errors import HttpError

from .commands import CommandHandler, NoticeStore
from .config import Settings
from .drive import DriveUploader
from .members import MemberManager
from .messages import MessageStore
from .post_process import PostProcessor
from .stack import StackManager
from .youtube_api import YouTubeClient
from .ytdlp import YtDlp, sanitize_title


class LiveBot:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.youtube = YouTubeClient(settings.youtube_token_path)
        self.drive = DriveUploader(settings.drive_token_path, settings.drive_folder_id)
        self.ytdlp = YtDlp(settings)
        self.messages = MessageStore(settings.auto_replies_path)
        self.stack = StackManager(settings.smoke_state_file, settings.stack_state_version)
        self.members = MemberManager(settings.member_file, settings.member_max_count)
        self.commands = CommandHandler(settings, self.messages, self.stack, self.members)
        self.notices = NoticeStore(settings)
        self.post_processor = PostProcessor(settings, self.youtube, self.drive, self.ytdlp)
        self.stop_event = threading.Event()

    def stop(self) -> None:
        self.stop_event.set()

    def connect_to_live(self) -> tuple[str, str, str]:
        while not self.stop_event.is_set():
            video_id = self.ytdlp.get_live_video_id()
            if not video_id:
                print("🔴 실시간 방송 감지 실패 → 300초 후 재시도")
                self.stop_event.wait(300)
                continue

            try:
                title = self.youtube.get_video_title(video_id)
                live_chat_id = self.youtube.get_live_chat_id(video_id)
            except Exception as exc:
                print(f"❌ 방송 정보 획득 실패: {exc} → 30초 후 재시도")
                self.stop_event.wait(30)
                continue

            if not title or not live_chat_id:
                print("❌ 방송 정보 획득 실패 → 30초 후 재시도")
                self.stop_event.wait(30)
                continue

            print(f"✅ 방송 연결 완료: {video_id} - {title}")
            return video_id, live_chat_id, title

        raise KeyboardInterrupt

    def _write_moderator_log(
        self,
        log_file,
        author_name: str,
        text: str,
        now_str: str,
    ) -> None:
        if "nightbot" in author_name.lower():
            return
        if any(word in text.lower() for word in ("시그1", "시그2", "시그3")):
            return
        line = f"[{now_str}] {author_name}: {text}\n"
        log_file.write(line)
        log_file.flush()
        print(f"🧩 [{now_str}] 모더레이터 기록됨: {author_name}: {text}")

    def _send_replies(self, live_chat_id: str, replies: list[str], command: str | None = None) -> None:
        for index, reply in enumerate(replies):
            if not reply:
                continue
            self.youtube.send_chat_message(live_chat_id, reply)
            if command == "!시그" and index < len(replies) - 1:
                time.sleep(1.0)
            elif index < len(replies) - 1:
                time.sleep(1.5)

    def _handle_periodic_messages(self, live_chat_id: str, current_time: float, last_hourly: float, last_mission: float):
        if current_time - last_hourly >= self.settings.hourly_interval:
            if self.messages.hourly_message:
                self.youtube.send_chat_message(live_chat_id, self.messages.hourly_message)
            last_hourly = current_time
            print("🕐 30분 자동 메시지 전송 완료")

        if current_time - last_mission >= self.settings.mission_interval:
            if self.messages.mission_message:
                self.youtube.send_chat_message(live_chat_id, self.messages.mission_message)
            last_mission = current_time
            print("🕐 50분 미션 전송 완료")

        return last_hourly, last_mission

    def _is_before_actual_start(self, published_at: str | None, actual_start_time: datetime | None) -> bool:
        if not published_at or not actual_start_time:
            return False
        message_time = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return message_time.timestamp() < actual_start_time.timestamp() - 10

    def run_forever(self) -> None:
        while not self.stop_event.is_set():
            video_id = live_chat_id = video_title = None
            log_path: Path | None = None
            try:
                video_id, live_chat_id, video_title = self.connect_to_live()
                actual_start_time = self.youtube.get_actual_start_time(video_id)
                today_str = datetime.now().strftime("%Y%m%d")
                log_path = self.settings.log_dir / f"{today_str}_{sanitize_title(video_title)}.txt"

                next_page_token = None
                last_upload_time = 0.0
                last_hourly_message_time = 0.0
                last_mission_message_time = 0.0
                last_end_check_time = 0.0
                consecutive_errors = 0

                with log_path.open("a", encoding="utf-8") as log_file:
                    while not self.stop_event.is_set():
                        current_time = time.time()

                        if current_time - last_end_check_time >= self.settings.end_check_interval:
                            last_end_check_time = current_time
                            if self.youtube.get_actual_end_time(video_id):
                                print("🟥 actualEndTime 확인됨: 방송 종료 확정")
                                break

                        try:
                            last_hourly_message_time, last_mission_message_time = self._handle_periodic_messages(
                                live_chat_id,
                                current_time,
                                last_hourly_message_time,
                                last_mission_message_time,
                            )
                        except Exception as exc:
                            print(f"⚠️ 주기적 메시지 전송 에러: {exc}")

                        try:
                            response = self.youtube.get_live_chat_messages(live_chat_id, next_page_token)
                            consecutive_errors = 0
                        except Exception as exc:
                            error_msg = str(exc)
                            consecutive_errors += 1
                            print(
                                f"[에러] 채팅 불러오기 실패 "
                                f"({consecutive_errors}/{self.settings.max_error_count}): {error_msg}"
                            )

                            if "503" in error_msg or "backenderror" in error_msg.lower():
                                self.stop_event.wait(7)
                                continue

                            try:
                                if self.youtube.get_actual_end_time(video_id):
                                    print("🟥 API 오류 후 actualEndTime 확인됨")
                                    break
                            except Exception:
                                pass

                            if consecutive_errors >= self.settings.max_error_count or "forbidden" in error_msg.lower():
                                print("🟥 방송 종료/권한 상실 의심 → actualEndTime 재확인")
                                try:
                                    if self.youtube.get_actual_end_time(video_id):
                                        break
                                except Exception:
                                    pass
                                self.stop_event.wait(10)
                                continue

                            self.stop_event.wait(10)
                            continue

                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        should_send_stack = False
                        should_send_members = False

                        for item in response.get("items", []):
                            snippet = item.get("snippet", {})
                            author_details = item.get("authorDetails", {})
                            text = snippet.get("displayMessage", "")
                            author_name = author_details.get("displayName", "알수없음")
                            is_moderator = author_details.get("isChatModerator", False)
                            published_at = snippet.get("publishedAt")

                            if self._is_before_actual_start(published_at, actual_start_time):
                                continue

                            if self.notices.handle_registration(text.strip(), is_moderator):
                                continue

                            result = self.commands.handle(text, is_moderator, actual_start_time)
                            if result.refresh_stack:
                                should_send_stack = True
                            if result.refresh_members:
                                should_send_members = True
                            if result.replies:
                                try:
                                    self._send_replies(live_chat_id, result.replies, result.command_name)
                                except Exception as exc:
                                    print(f"⚠️ 명령어 응답 전송 실패: {exc}")

                            notice_reply = self.notices.handle_lookup(text.strip()) if self.commands.can_send(text.strip()) else None
                            if notice_reply:
                                try:
                                    self.youtube.send_chat_message(live_chat_id, notice_reply)
                                except Exception as exc:
                                    print(f"⚠️ 공지 응답 전송 실패: {exc}")

                            if is_moderator and text:
                                self._write_moderator_log(log_file, author_name, text, now_str)

                            if text.strip() == "!후원" and self.commands.can_send("!후원"):
                                if self.messages.donation_message.strip():
                                    self.youtube.send_chat_message(live_chat_id, self.messages.donation_message)

                        if should_send_stack:
                            time.sleep(2)
                            stack_text = self.stack.format_text()
                            if stack_text:
                                self.youtube.send_chat_message(live_chat_id, stack_text)

                        if should_send_members:
                            time.sleep(2)
                            member_text = self.members.format_text()
                            if member_text:
                                self.youtube.send_chat_message(live_chat_id, member_text)

                        if time.time() - last_upload_time > 300:
                            try:
                                self.drive.upload_or_update(log_path)
                            except Exception as exc:
                                print(f"⚠️ 주기적 로그 업로드 실패: {exc}")
                            last_upload_time = time.time()

                        next_page_token = response.get("nextPageToken")
                        polling_raw = response.get("pollingIntervalMillis")
                        polling_interval = max(
                            float(polling_raw) / 1000.0 if polling_raw else 7.0,
                            3.0,
                        )
                        self.stop_event.wait(polling_interval)
            except KeyboardInterrupt:
                self.stop()
                raise
            except HttpError as exc:
                print(f"❌ YouTube API 오류: {exc}")
            except Exception as exc:
                print(f"❌ 메인 루프 오류: {exc}")
            finally:
                if video_id and video_title and log_path and not self.stop_event.is_set():
                    print("🛑 방송 종료 감지 → 사후처리 스레드 시작")
                    self.post_processor.start(video_id, video_title, log_path)

                if not self.stop_event.is_set():
                    self.stop_event.wait(1)
