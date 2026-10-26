TamilCartoons — Complete project / Android setup
26 October 2026

STATUS
Files are prepared. This is NOT an already-deployed service.
The real Render service URL has not been provided, so backendUrl is deliberately
empty and the player shows a clear setup error. No invented service address is used.
The supplied Supabase publishable key is reused and worked for all three public
REST data endpoints (HTTP 200). Read-only row keys confirm all supplied columns.
The OpenAPI schema endpoint returned 401, so privileged schema, policies, function
implementation, constraints and admin membership still require SQL inspection.
No production database changes were executed.

FIRST STEP — DO THIS NOW ON YOUR PHONE
1. Extract this ZIP on your phone.
2. Open Supabase → SQL Editor → New query.
3. Paste and run sql/00_inspect.sql from the extracted project. It only reads schema
   and policy information. Keep the results privately for the migration checks.
The existing public key works; no key replacement is currently needed.
Never send Telegram credentials, passwords, OTPs or sessions in chat.
Then follow the numbered phases below, one phase at a time.

WHAT IS PRESERVED
admin.html is the uploaded 1,778-line dashboard, extended rather than replaced.
Anime CRUD, seasons CRUD, episodes edit/delete, Telegram link parsing, bulk import,
Saved Items and Supabase password sign-in remain present. Added is_app_admin() RPC
check, one-time startup, paginated cache loading and optional catalogue metadata.
Server still uses Pyrogram stream_media with 1 MiB chunk offsets and first-chunk
slicing; multiple episodes now work instead of one hardcoded global message.
The backend's embedded demo player has moved to the dedicated frontend player.
Your uploaded originals are untouched. This package is one new project edition.

PROJECT ROOT — ONE REPOSITORY
index.html
anime.html
player.html
admin.html
assets/css/app.css
assets/js/config.js
assets/js/common.js
assets/js/index.js
assets/js/anime.js
assets/js/player.js
sql/00_inspect.sql
sql/01_metadata.sql
sql/02_admin_guard.sql
sql/03_optional_admin_write_policies.sql
telegram-backend/ (all contents listed below)
render.yaml
.gitignore
README_SETUP.txt
DEPLOY_MOBILE_TAMIL.txt
TROUBLESHOOTING.txt
VALIDATION_REPORT.txt

USE YOUR EXISTING REPOSITORY
https://github.com/arulmani94/tamilcartoons-app
Website: https://arulmani94.github.io/tamilcartoons-app/
Extract the ZIP first; uploading only the ZIP does not deploy its contents.
Upload the CONTENTS of the TamilCartoons folder to the repository root.
Do not accidentally create /TamilCartoons/index.html inside the repository.
The existing index(2).html upload becomes index.html. Use index.html going forward.
Keep a private backup / Git history before replacing your existing source.

PHASE 1 — DATABASE (PHONE BROWSER)
1. Supabase → SQL Editor → New query.
2. Run sql/00_inspect.sql. It reads columns, policies, function definition and FKs.
3. Verify anime, seasons and episodes columns match the supplied requirements.
   Verify is_app_admin() checks auth.uid() against trusted membership. An SQL owner
   should fix a missing/incorrect function before proceeding; its contents were not
   supplied, so this package does not invent a new app_admins schema or membership.
4. Run sql/01_metadata.sql. It adds category, genre, status, studio, rating,
   is_trending and non-unique query indexes only. It does not classify old records.
5. Run sql/02_admin_guard.sql after inspecting current policies. It adds restrictive
   admin-only write guards and anonymous write denials to all four existing tables.
   It retains existing policies; an existing permissive admin write policy is still
   necessary. If none exists, verify the existing function first, then run
   sql/03_optional_admin_write_policies.sql. Do not disable RLS.
6. Existing Supabase Auth account + existing app_admins membership are required.
   The website has no signup or hardcoded password. The initial admin is provisioned
   privately by the project owner, not through an unauthenticated frontend.
7. Admin → Saved Items → Edit Anime → enable Save catalogue metadata; set Category
   to Tamil Dubbed / Tamil / Tamil Dubbed Anime. Select Trending if appropriate.
   Save. Existing uncategorized records still appear under All titles.
   Genre, studio, status and rating appear on details only when populated.
   Trending is an editor selection, not a fabricated view-count algorithm.

IMPORTANT DATABASE LIMITS
No SQL was run against your live database. Migration is transactional and repeatable.
The guard does not replace existing permissive policies. A failed function/RLS check
will reject writes. Use 00_inspect to diagnose, never solve it by disabling RLS.
Foreign-key cascade behavior is preserved. If deletion reports a FK error, delete
child episodes then child seasons in Saved Items, then the anime; do not assume the
uploaded schema guarantees cascade. No records are deleted by setup scripts.

PHASE 2 — TELEGRAM AUTHORIZATION (ONE TIME, PRIVATE)
The existing .session metadata identifies a USER session, not a bot session.
TG_API_ID and TG_API_HASH alone do not authorize a new server.
The uploaded session/credentials were NOT used to log into Telegram here.
Do not commit .env, *.session, *.session-journal, or session strings to GitHub.
A session string grants account access. Keep it only in private environment settings.

Recommended Android path: trusted Termux installation, NOT a public online notebook.
If you already have Python in a trusted terminal, use that instead.
1. In Termux install Python: pkg update && pkg install python
2. Put telegram-backend/export_session.py and requirements.txt in a PRIVATE folder.
3. Install session-tool dependencies:
   python -m pip install Pyrogram==2.0.106 python-dotenv==1.0.1
   TgCrypto is optional for this one-time export. No need to build it on Android.
4. Run: python export_session.py
5. Enter your own API ID/hash privately in the terminal. For a new session leave
   existing-session path blank. Complete Telegram phone / OTP / 2FA prompts there.
   To reuse your existing working file, STOP its other clients first and give its
   private absolute path WITHOUT .session. Do not upload it to any repository.
6. Copy private_session_string.txt contents to Render TG_SESSION_STRING.
7. Delete the private output file after saving it in the environment/password vault.
8. Use a session/account with access to the video channels. After restarts the server
   loads dialogs to resolve numeric private-channel peers into its in-memory cache.
9. Do not run multiple deployments/workers using the same authorization at once.
   If replacing an old service, stop the old instance before starting the new one.
For an invalid/revoked session, export a new session privately and update Render.

PHASE 3 — UPLOAD FRONTEND AND BACKEND
Frontend files used by GitHub Pages:
  index.html, anime.html, player.html, admin.html, entire assets/ directory.
Backend files used by Render under telegram-backend/:
  stream_server.py, requirements.txt, Dockerfile, .dockerignore, .gitignore,
  .env.example (EMPTY template), export_session.py, find_channel.py, test_video.py.
Developer checks (not required in container): requirements-test.txt and tests/.
Repo root also contains render.yaml for optional Blueprint deployment.
SQL and TXT instructions can remain in the repo; they contain no real secrets.
DO NOT upload the source attachment .env or either Telegram session attachment.
.gitignore cannot remove secrets already committed: remove any existing tracked
secrets and revoke exposed Telegram authorizations before using a replacement.
Docker uses an explicit three-file allowlist, so sessions are not copied to the image.
GitHub Pages → Settings → Pages → Deploy from a branch → main → /(root).
If your existing active branch is named differently, select that branch, not a new one.
All links are relative and work under /tamilcartoons-app/.

PHASE 4 — RENDER CONFIGURATION (MANUAL DOCKER)
Render → New → Web Service → select the existing GitHub repository.
Name: tamilcartoons-stream (or your existing service name)
Branch: the branch containing the new files
Root Directory: telegram-backend
Runtime / Language: Docker
Dockerfile Path: ./Dockerfile (relative to root directory)
Docker Build Context: . (relative to root directory)
Docker Command override: leave empty (Dockerfile CMD starts server)
Build Command / Start Command: leave empty for Docker
Health Check Path: /health
Instance: Free for trials; choose suitable paid compute for production requirements
Port: Render supplies PORT; app binds 0.0.0.0 and uses PORT (fallback 10000)
Workers: exactly 1
A native Python service must be recreated/changed to Docker if runtime switching is
not supported in your dashboard. Do not leave an old native build command selected.
For a Blueprint instead, choose root render.yaml; do NOT create a second service
if you already configured the manual service. Blueprint rootDir matches this layout.

RENDER ENVIRONMENT — EXACT NAMES
TG_API_ID            Your own Telegram numeric API ID
TG_API_HASH          Your own Telegram API hash (secret)
TG_SESSION_STRING    Authorized Pyrogram session string (secret)
TG_ALLOWED_CHANNELS  Comma-separated -100 channel IDs and/or @channel_usernames
FRONTEND_ORIGINS     https://arulmani94.github.io
PORT                 Normally provided by Render; do not override unless needed
LOG_LEVEL            Optional; INFO is the default
No TG_BOT_TOKEN or Supabase service-role key is used by this backend.
TG_ALLOWED_CHANNELS must include the EXACT identifier form saved in episodes.
For public links saved as @name, allow @name as well as a numeric ID if both are used.
CORS is an origin: no /tamilcartoons-app/ path and no trailing slash.
CORS is browser access control, not user authentication or billing protection.
Allowlist limits the Telegram chats that can be served, including non-browser callers.
Any message with video media inside an allowed channel can be requested by ID.
Use channels dedicated to your public catalogue. This package does not add viewer
accounts, signed playback tickets, DRM, or per-episode private entitlements.

PHASE 5 — CONNECT FRONTEND TO REAL BACKEND
1. Deploy Render; inspect logs. Open the EXACT assigned Render URL + /health.
2. Required response: HTTP 200 and {"status":"ok","telegram_ready":true}.
   If 503 or deployment is unhealthy, fix environment/session/channel access first.
3. Copy the actual Render origin shown on your dashboard (HTTPS, no path).
4. Edit assets/js/config.js: set backendUrl from '' to that real origin.
   Do not paste an example address. Do not use localhost, 127.0.0.1 or a /video path.
5. Commit that single config change; wait for GitHub Pages deployment; hard-refresh.
6. Open a title → switch season → choose episode → Play → seek forward/back.
7. Verify Previous at first episode is disabled and Next at last episode is disabled.
8. Test on Android Chrome and desktop with a known MP4 (H.264 video / AAC audio).

PLAYBACK AND HOSTING LIMITATIONS
This is raw HTTP byte streaming, not transcoding. Content-Type comes from Telegram
media MIME or filename; the backend does not label every file as MP4.
A .mkv/HEVC/DTS/other incompatible source may fail in a browser even with correct
HTTP ranges. Convert your source to an appropriate single-audio MP4 before upload
(or add a separately tested transcoding pipeline later). No audio-track selector,
subtitles/upload controls, iframe, or download button is included.
An HTML5 player cannot directly play arbitrary Google Drive share URLs or Telegram
web URLs. It uses /video with selected, validated channel/message identifiers.
Hiding download controls is not DRM; any public stream can be saved by a client.
Render free services can sleep after 15 minutes without inbound traffic and can take
about a minute to wake. Filesystem writes are ephemeral. Session strings avoid
reliance on a local SQLite file; Telegram can still revoke authorization.
Bandwidth, resource, concurrent viewer and Telegram rate limits remain real.
Long streams can be interrupted by deploys, restarts, host/network timeouts or
Telegram errors. This project does not promise uninterrupted or unlimited viewing.
No disk caching of full files; memory is bounded by chunks per concurrent stream.
Use one worker. Scale only after measuring and arranging separate authorizations.
Pyrogram 2.0.106 is retained for compatibility; the original project is archived.
A future Telegram layer change may require an explicitly tested maintained fork.

DEVELOPER CHECKS (OPTIONAL ON PHONE)
cd telegram-backend
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m pytest tests -q
Docker check from the repository root on a Docker-capable computer:
docker build -t tamilcartoons-stream telegram-backend
Docker image needs the private environment supplied at runtime, not at build time.
See VALIDATION_REPORT.txt for the tests actually run in preparation.

OFFICIAL REFERENCES (checked 26 October 2026)
https://render.com/docs/free
https://render.com/docs/web-services
https://render.com/docs/blueprint-spec
https://docs.pyrogram.org/api/methods/stream_media
https://docs.pyrogram.org/topics/storage-engines
https://docs.pyrogram.org/api/client
https://github.com/pyrogram/pyrogram
