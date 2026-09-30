# Authentication

This project uses Google OAuth 2.0 authorized-user token JSON files.

## YouTube

Set:

```env
YOUTUBE_TOKEN_PATH=./credentials/youtube_token.json
```

The token must contain permission for the YouTube API scope used by the bot.

## Google Drive

Set:

```env
GOOGLE_DRIVE_TOKEN_PATH=./credentials/drive_token.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

The Drive token is intentionally separate from the YouTube token in this refactored version. This avoids relying on the old configuration name `SERVICE_ACCOUNT_FILE`, which was misleading because the original code loaded it with `Credentials.from_authorized_user_file()` rather than service-account credentials.

## Important

Never commit the token files, OAuth client secrets, or browser cookies. They are ignored by `.gitignore` and should stay under the local `credentials/` directory.
