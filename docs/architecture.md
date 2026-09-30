# Architecture

```text
YouTube Live
    │
    ▼
LiveBot (bot.py)
    ├── YouTubeClient       → YouTube Data API
    ├── YtDlp                → live detection / post-stream chat download
    ├── CommandHandler       → chat commands
    ├── NoticeStore          → notice/location/money text files
    ├── StackManager         → smoke/food state
    ├── MemberManager        → member scoreboard
    ├── DriveUploader        → periodic log upload
    └── PostProcessor        → JSON analysis → highlight comment
```

The main goal is to keep the live polling loop small and move stateful or external-service logic into dedicated modules.
