TamilCartoons Telegram backend

Canonical phone-friendly instructions: ../README_SETUP.txt and
../DEPLOY_MOBILE_TAMIL.txt at the repository root. One repository is used for Pages
and Render; do not create a second competing backend service.

Render manual values:
Root Directory = telegram-backend
Runtime = Docker
Dockerfile Path = ./Dockerfile
Docker Build Context = .
Docker Command override = empty
Health Check Path = /health
One process / one Uvicorn worker.
The Dockerfile starts python stream_server.py; 0.0.0.0 and environment PORT are used.

Required private environment:
TG_API_ID
TG_API_HASH
TG_SESSION_STRING
TG_ALLOWED_CHANNELS (comma-separated channel IDs / @usernames)
FRONTEND_ORIGINS=https://arulmani94.github.io

An authorized Pyrogram user session is required. Privately run export_session.py
once on a trusted terminal/Termux; API ID/hash alone is insufficient.
Never commit .env, private_session_string.txt, or any *.session* files.
.env.example has empty credentials and is safe to commit.
Do not export an authorization while another server is using the same session.

GET /health returns 200 when connected, 503 when not ready.
GET or HEAD /video?channel_id=...&message_id=... serves selected media.
GET accepts a single Range: bytes=... header, with HTTP 206 or 416 as appropriate.
Channel allowlist is enforced independently of CORS. No interactive web login.

Local setup (private environment):
python -m pip install -r requirements.txt
python stream_server.py

Developer tests (mock Telegram, mock Supabase):
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m pytest tests -q

The original config.py hardcoded one channel/message. It is no longer required:
stream_server.py uses environment settings and request identifiers; updated
find_channel.py and test_video.py also read environment directly.
Do not copy the old hardcoded config.py or the embedded backend player back over
this release. The dedicated player.html handles public playback.
