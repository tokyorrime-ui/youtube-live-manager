# YouTube Live Automation Bot

A Python-based automation bot for YouTube Live streams.

This project monitors YouTube Live Chat, handles moderator commands, sends scheduled messages, manages lightweight stream state, uploads logs to Google Drive, and performs post-stream chat analysis.

## Features

* YouTube Live Chat polling
* Moderator-only command handling
* Custom auto-replies
* `!uptime` based on the actual stream start time
* Smoke / food stack management
* Member scoreboard management
* Notice, location, and money message registration
* Periodic Google Drive log uploads
* Post-stream live-chat download with `yt-dlp`
* 10-second bucket-based highlight analysis
* Automatic highlight comment posting
* Windows sleep prevention while the bot is running
* Automated tests
* GitHub Actions CI

## Project Structure

```text
youtube-live-automation-bot/
├─ .github/
│  └─ workflows/
│     └─ ci.yml
│
├─ config/
│  ├─ auto_replies.json.example
│  └─ auto_replies.json          # local only
│
├─ credentials/                  # local only
│  ├─ youtube_token.json
│  ├─ drive_token.json
│  └─ cookies.txt
│
├─ data/
│  ├─ analysis/
│  ├─ live_logs/
│  ├─ notices/
│  └─ state/
│
├─ docs/
│  ├─ architecture.md
│  ├─ authentication.md
│  ├─ migration.md
│  └─ setup.md
│
├─ src/
│  └─ youtube_live_bot/
│     ├─ analysis.py
│     ├─ app.py
│     ├─ bot.py
│     ├─ commands.py
│     ├─ config.py
│     ├─ drive.py
│     ├─ members.py
│     ├─ messages.py
│     ├─ post_process.py
│     ├─ stack.py
│     ├─ system.py
│     ├─ youtube_api.py
│     └─ ytdlp.py
│
├─ tests/
├─ tools/
├─ .env.example
├─ .gitignore
├─ LICENSE
├─ pyproject.toml
├─ requirements.txt
└─ README.md
```

## Requirements

* Windows
* Python 3.13+
* YouTube Data API v3
* Google OAuth 2.0
* `yt-dlp`
* Node.js runtime for the `yt-dlp` configuration used by this project
* Google Drive API
* A valid YouTube account with permission to use the target live chat

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/youtube-live-automation-bot.git
cd youtube-live-automation-bot
```

### 2. Create a virtual environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -e ".[dev]"
```

## Local Configuration

This project keeps machine-specific settings and private credentials outside the public source code.

### 1. Create `.env`

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set your local paths, channel URL, Google Drive folder ID, and other runtime settings.

### 2. Create the credentials directory

```powershell
New-Item -ItemType Directory -Force credentials
```

Place your private credential files inside it:

```text
credentials/
├─ youtube_token.json
├─ drive_token.json
└─ cookies.txt
```

These files are local secrets and must never be committed to GitHub.

See [`docs/authentication.md`](docs/authentication.md) for authentication details.

### 3. Create the local auto-reply configuration

```powershell
Copy-Item config\auto_replies.json.example config\auto_replies.json
```

Edit `config/auto_replies.json` to configure channel-specific messages such as:

* `!시그`
* `!메뉴`
* scheduled messages
* donation messages

The local `auto_replies.json` file is ignored by Git.

## Run the Bot

After configuration:

```powershell
python -m youtube_live_bot
```

The bot will monitor the configured channel for an active live stream and begin processing chat messages when a stream is detected.

## Commands

### Stack Management

```text
!스택
!스택 설정 금연30
!스택 추가 금연10
!스택 삭제 금연5
!스택 시간
!스택 시간 13:20
!스택 삭제 시간
```

### Member Management

```text
!멤버
!멤버 추가 멤버A375
!멤버 삭제 멤버A 100
!멤버 제거 멤버A
```

### Notices and Messages

```text
!공지
!알리미 등록 방송 관련 공지 내용
!위치
!위치 등록 현재 위치 정보
!용돈
!용돈 등록 안내 내용
!후원
```

### Stream Information

```text
!uptime
```

### Auto Replies

```text
!시그
!메뉴
```

Auto-reply text is loaded from `config/auto_replies.json`.

## Post-Stream Processing

After a live stream ends, the bot can:

1. Upload the local log to Google Drive.
2. Download the official live-chat replay using `yt-dlp`.
3. Analyze chat activity in 10-second buckets.
4. Detect predefined highlight patterns.
5. Generate a highlight summary.
6. Post the generated highlight as a YouTube comment.
7. Remove the temporary downloaded chat JSON.

The post-processing workflow is documented in [`docs/architecture.md`](docs/architecture.md).

## Security

Do not commit any of the following:

```text
.env
credentials/
*.json
cookies*.txt
runtime logs
private channel configuration
API keys
OAuth client secrets
personal donation or bank-account information
```

The repository includes a `.gitignore` that excludes common credential and runtime-data paths.

Before pushing to GitHub, always check:

```powershell
git status
git add .
git status
```

Make sure no private credentials or local-only configuration files are staged.

## Development

Run tests:

```powershell
pytest -q
```

Run Ruff:

```powershell
ruff check src tests
```

## Documentation

* [`docs/setup.md`](docs/setup.md) — detailed setup instructions
* [`docs/authentication.md`](docs/authentication.md) — YouTube / Google authentication
* [`docs/architecture.md`](docs/architecture.md) — application architecture
* [`docs/migration.md`](docs/migration.md) — migration from the original single-file implementation

## License

MIT License
