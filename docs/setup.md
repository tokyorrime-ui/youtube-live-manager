# Setup

## 1. Create a virtual environment

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## 2. Copy environment settings

```powershell
Copy-Item .env.example .env
Copy-Item config\auto_replies.json.example config\auto_replies.json
```

Then edit `.env` and `config/auto_replies.json` locally. The example intentionally does not contain the original personal bank-account message; put any private donation text only in the ignored local file.

## 3. Put credentials outside Git

Create:

```text
credentials/
├─ youtube_token.json
├─ drive_token.json
└─ cookies.txt
```

These files are ignored by Git.

## 4. Put yt-dlp in your local tools directory

Set `YTDLP_PATH` in `.env` to the executable path you actually use.

## 5. Run tests

```powershell
pytest -q
```

## 6. Start the bot

```powershell
python -m youtube_live_bot
```

or:

```powershell
youtube-live-bot
```
