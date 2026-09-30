"""Google Drive log uploader."""

from __future__ import annotations

from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"


class DriveUploader:
    def __init__(self, token_path: Path, folder_id: str):
        self.token_path = token_path
        self.folder_id = folder_id.strip()
        self.service = None

    def _ensure_service(self):
        if self.service is not None:
            return self.service
        if not self.folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID is not configured.")
        if not self.token_path.exists():
            raise FileNotFoundError(f"Google Drive OAuth token not found: {self.token_path}")
        credentials = Credentials.from_authorized_user_file(
            str(self.token_path), [DRIVE_SCOPE]
        )
        self.service = build("drive", "v3", credentials=credentials)
        return self.service

    def upload_or_update(self, local_file_path: Path) -> None:
        service = self._ensure_service()
        file_name = local_file_path.name
        media = MediaFileUpload(str(local_file_path), resumable=True)
        file_metadata = {"name": file_name, "parents": [self.folder_id]}

        try:
            existing_files = (
                service.files()
                .list(
                    q=(
                        f"name='{file_name}' and '{self.folder_id}' in parents "
                        "and trashed=false"
                    ),
                    spaces="drive",
                    fields="files(id, name)",
                )
                .execute()
                .get("files", [])
            )

            if existing_files:
                service.files().update(
                    fileId=existing_files[0]["id"], media_body=media
                ).execute()
                print(f"🔁 기존 파일 업데이트 완료: {file_name}")
                return

            service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            print(f"☁️ 새 파일 업로드 완료: {file_name}")
        except (HttpError, OSError, ConnectionAbortedError, ConnectionResetError) as exc:
            print(f"⚠️ Google Drive 업로드 실패: {exc}")
