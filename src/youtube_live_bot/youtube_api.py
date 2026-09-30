"""Thin wrapper around the YouTube Data API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import Resource, build
from google.oauth2.credentials import Credentials

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"


class YouTubeClient:
    def __init__(self, token_path: Path):
        self.token_path = token_path
        self.service = self._build_service()

    def _build_service(self) -> Resource:
        if not self.token_path.exists():
            raise FileNotFoundError(
                f"YouTube OAuth token not found: {self.token_path}\n"
                "Create the token locally and keep it outside Git."
            )
        credentials = Credentials.from_authorized_user_file(
            str(self.token_path), [YOUTUBE_SCOPE]
        )
        return build("youtube", "v3", credentials=credentials)

    def get_live_chat_id(self, video_id: str) -> str | None:
        response = self.service.videos().list(
            part="liveStreamingDetails", id=video_id
        ).execute()
        items = response.get("items", [])
        if not items:
            return None
        return items[0].get("liveStreamingDetails", {}).get("activeLiveChatId")

    def get_video_title(self, video_id: str) -> str | None:
        response = self.service.videos().list(part="snippet", id=video_id).execute()
        items = response.get("items", [])
        return items[0].get("snippet", {}).get("title") if items else None

    def get_actual_start_time(self, video_id: str) -> datetime | None:
        return self._get_actual_time(video_id, "actualStartTime")

    def get_actual_end_time(self, video_id: str) -> datetime | None:
        return self._get_actual_time(video_id, "actualEndTime")

    def _get_actual_time(self, video_id: str, field: str) -> datetime | None:
        response = self.service.videos().list(
            part="liveStreamingDetails", id=video_id
        ).execute()
        items = response.get("items", [])
        if not items:
            return None
        timestamp = items[0].get("liveStreamingDetails", {}).get(field)
        if not timestamp:
            return None
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def get_live_chat_messages(
        self, live_chat_id: str, page_token: str | None = None
    ) -> dict:
        return (
            self.service.liveChatMessages()
            .list(
                liveChatId=live_chat_id,
                part="snippet,authorDetails",
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )

    def send_chat_message(self, live_chat_id: str, message_text: str) -> None:
        self.service.liveChatMessages().insert(
            part="snippet",
            body={
                "snippet": {
                    "liveChatId": live_chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {"messageText": message_text},
                }
            },
        ).execute()

    def post_video_comment(self, video_id: str, comment_body: str) -> None:
        self.service.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {"snippet": {"textOriginal": comment_body}},
                }
            },
        ).execute()
