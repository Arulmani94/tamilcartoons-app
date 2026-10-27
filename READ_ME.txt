V12 playback handoff + timeout fix

Replace these THREE files in your existing GitHub repo, preserving paths:
player.html
assets/js/player.js
telegram-backend/stream_server.py

Keep existing assets/js/vendor/hls.min.js from V11. Do not replace config.js or secrets.
Commit. Deploy latest commit on Render and wait until Live.
Wait for Vercel frontend deployment Ready. Hard refresh the video page.

Changes:
Prefer Hls.js on MSE-capable browsers; native HLS remains fallback for Safari.
Start playback after manifest parsing, rather than during media attachment.
Let Hls.js own its playback errors; stale native video errors no longer replace its state.
Retry restarts streaming instead of pointing the browser at the incompatible original.
A format inspection timeout falls back to streaming startup.
Reuse existing HLS jobs for metadata/startup. Serve generated segments without
querying Telegram for each two-second segment; channel allowlist still checked.

Verification: 35 backend tests passed, 18 browser regression tests passed.
Real server first HLS segment fetched and ffprobe verified H.264/AAC.
The extra actual H.264 browser decoding test was skipped because the local Chromium
build lacks those codecs; production end-to-end playback remains to be verified
after upload. No claim of live deployment or production playback confirmation.
