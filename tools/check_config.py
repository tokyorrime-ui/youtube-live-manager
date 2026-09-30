from pathlib import Path
import os

from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env")

required = [
    "YOUTUBE_CHANNEL_URL",
    "YOUTUBE_TOKEN_PATH",
    "GOOGLE_DRIVE_FOLDER_ID",
    "YTDLP_PATH",
    "COOKIE_SOURCE",
]

missing = [name for name in required if not os.getenv(name, "").strip()]
if missing:
    print("Missing configuration:")
    for name in missing:
        print(f"  - {name}")
    raise SystemExit(1)

print("Configuration basics look OK.")
