# Migration from the original single-file bot

The supplied implementation mixed configuration, YouTube API access, chat handling, persistence, yt-dlp collection, and post-processing in one large file. The refactored project separates those responsibilities.

## Configuration mapping

| Original concept | Refactored setting |
|---|---|
| `SERVICE_ACCOUNT_FILE` | `GOOGLE_DRIVE_TOKEN_PATH` |
| `TOKEN_PATH` | `YOUTUBE_TOKEN_PATH` |
| `YTDLP_PATH` | `YTDLP_PATH` |
| `CHANNEL_URL` | `YOUTUBE_CHANNEL_URL` |
| `FOLDER_ID` | `GOOGLE_DRIVE_FOLDER_ID` |
| `BASE_DIR` | `BOT_DATA_DIR` |
| `AUTO_REPLIES` | `config/auto_replies.json` |

The old variable name `SERVICE_ACCOUNT_FILE` was misleading because the original source loaded the file with `Credentials.from_authorized_user_file()`. The refactor uses the clearer authorized-user token name `GOOGLE_DRIVE_TOKEN_PATH`.

## Existing runtime data

The default data directory is `./data`. To continue using an existing local data directory, set for example:

```env
BOT_DATA_DIR=C:/path/to/your/old/sisugiritlog
```

The bot will continue using that directory for the live logs, notice files, stack state, and member state.

## Auto-reply migration

Copy the example file:

```powershell
Copy-Item config\auto_replies.json.example config\auto_replies.json
```

Then restore your channel-specific `!시그`, `!메뉴`, and donation message locally. Do not publish private financial or authentication data.
