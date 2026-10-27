TamilCartoons V11: Progressive Streaming Fix

Upload these files into the EXISTING GitHub repository, preserving their folder paths.
Do not upload the ZIP itself or create a new top-level folder.

Replace player.html, assets/js/player.js, telegram-backend/stream_server.py,
and telegram-backend/Dockerfile.
Add assets/js/vendor/hls.min.js and assets/js/vendor/hls-LICENSE.

Commit all changes. Both Render backend and Vercel frontend must deploy latest commit.
Render: Docker, root telegram-backend, one worker, port 10000 ($PORT).
If auto-deploy is disabled: Manual Deploy > Deploy latest commit.
Keep existing config.js, requirements.txt and environment variables.
FRONTEND_ORIGINS must include https://tamilcartoons-app-seven.vercel.app

Browser-compatible MP4 streams directly. Other videos use HLS segments generated
while Telegram bytes arrive. Playback starts before a complete source download.
HLS starts at the beginning; seeking is limited to already-generated segments.
The seekable timeline grows during processing. Compatibility encoding is capped
at 720p with AAC audio. Autoplay may require tapping Play.

Free Render cold starts, Telegram transfer speed and server CPU still affect speed.
One compatibility encoder runs at once; viewers of the same episode share output.
Different episodes can queue. Concurrent traffic needs a larger server and ideally
pre-encoded persistent HLS storage/CDN. Cache is temporary and restarts regenerate it.
Default generated output limit: 1 GiB. Damaged/DRM/unusual files may not work.

Tests: 33 backend + 18 browser checks passed. Throttled HTTP input verified
first playable H.264 segment appeared before the source transfer finished.
Production Telegram playback must be verified after deployment.
