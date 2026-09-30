# YouTube Live Automation Bot

Python-based automation bot for YouTube Live streams.

This project monitors a live chat, handles moderator commands, sends scheduled messages, stores simple stream state, uploads logs to Google Drive, and performs post-stream live-chat analysis.

## Features

- YouTube Live Chat polling
- Moderator command handling
- Custom auto-replies
- `!uptime` calculation based on actual stream start time
- Smoke / food stack management
- Member scoreboard management
- Notice / location / money message registration
- Periodic Google Drive log upload
- yt-dlp based post-stream live-chat download
- 10-second bucket highlight analysis
- Automatic highlight comment posting
- Windows sleep prevention while running
- Local tests and GitHub Actions CI

## Project structure

```text
src/youtube_live_bot/
├─ analysis.py       # Post-stream chat analysis
├─ app.py            # Console entry point
├─ bot.py            # Live monitoring loop
├─ commands.py       # Chat command handling
├─ config.py         # Environment-based configuration
├─ drive.py          # Google Drive uploader
├─ members.py        # Member scoreboard state
├─ messages.py       # Local auto-reply configuration
├─ post_process.py   # Post-stream processing
├─ stack.py          # Smoke / food stack state
├─ system.py         # OS helpers
├─ youtube_api.py    # YouTube Data API wrapper
└─ ytdlp.py          # yt-dlp integration
```

## Quick start

### 1. Clone the repository

git clone https://github.com/YOUR_USERNAME/youtube-live-automation-bot.git
cd youtube-live-automation-bot

### 2. Create a Python environment

py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"

### 3. Create local configuration

Copy-Item .env.example .env
Copy-Item config\auto_replies.json.example config\auto_replies.json
New-Item -ItemType Directory -Force credentials

### 4. Add your private credentials

Put your local credential files here:

credentials/
├─ youtube_token.json
├─ drive_token.json
└─ cookies.txt

These files are private and must never be committed to GitHub.

### 5. Edit `.env`

Set your channel URL, yt-dlp path, Google Drive folder ID, and other local settings.

### 6. Run tests

pytest -q

### 7. Start the bot

python -m youtube_live_bot

See:

- [`docs/setup.md`](docs/setup.md)
- [`docs/authentication.md`](docs/authentication.md)
- [`docs/architecture.md`](docs/architecture.md)

## Configuration

Secrets and local machine paths are intentionally excluded from source code.

Use `.env` for paths and runtime settings, and `config/auto_replies.json` for channel-specific messages.

### Important security rule

Do **not** commit:

- OAuth token JSON files
- OAuth client secrets
- YouTube / Google API keys
- Browser cookies
- Personal donation or bank-account information
- Runtime logs containing private user information

The included `.gitignore` blocks the common credential and runtime-data locations.

## Commands

The refactored bot preserves the command families in the supplied implementation:

```text
!스택
!스택 설정 금연30
!스택 추가 금연10
!스택 삭제 금연5
!스택 시간
!스택 시간 13:20
!스택 삭제 시간

!멤버
!멤버 추가 멤버A375
!멤버 삭제 멤버A 100
!멤버 제거 멤버A

!공지
!공지 registration: !알리미 등록 ...
!위치
!용돈
!후원
!uptime
!시그
!메뉴
```

`!시그`, `!메뉴`, scheduled messages, and donation text are now loaded from `config/auto_replies.json` rather than being hard-coded in Python.

Copy `config/auto_replies.json.example` to `config/auto_replies.json` and customize it locally. The real file is ignored by Git so channel-specific text does not have to be public.

## Google Drive authentication note

The original code used a variable named `SERVICE_ACCOUNT_FILE`, but loaded that file with `Credentials.from_authorized_user_file()`. That is not service-account authentication. This refactor uses the clearer name `GOOGLE_DRIVE_TOKEN_PATH` for the authorized-user token file.

## Development

Run tests:

```powershell
pytest -q
```

Run Ruff:

```powershell
ruff check src tests
```

## License

MIT
