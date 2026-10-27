TamilCartoons V13 — Duration, faster remux and automatic Telegram thumbnails

INSTALL
Extract ZIP. Upload the three files to your existing repository, preserving paths:
  player.html
  assets/js/player.js
  telegram-backend/stream_server.py
Commit, deploy latest commit on Render, wait for Live. Wait for Vercel Ready.
Hard refresh the player (Ctrl+Shift+R). Keep V11 vendor/hls.min.js and Dockerfile.
Do not change config.js, requirements.txt or private environment values.

WHAT CHANGED
Full duration comes from Telegram video metadata, or original container probing.
Partial HLS playlist length is never presented as full episode duration. When
original duration cannot be determined, '--:--' is shown rather than a false total.
Seeking uses full duration for the slider and separately checks available segments;
a request past generated video shows an explanation rather than an incorrect jump.

H.264 8-bit / AAC videos are remuxed into HLS without encoding video or audio again.
Other codecs convert only the tracks that need it. At most two streaming jobs run,
with one CPU-intensive transcoder. Startup waits for three segments (or a completed
short video) for a small buffer. Metadata, format and thumbnails are bounded caches.

Episode thumbnails are taken automatically from the Telegram video's thumbnail.
Telegram thumbnails with unknown size are accepted with a strict downloaded-size
limit. Only the small preview is downloaded, not the original video. If Telegram
has no usable thumbnail, the existing post photo remains the fallback. There is
no need to select a separate episode photo. No poster is added inside the player.

VERIFICATION
38 backend tests passed including genuine H.264/AAC MKV remux, MPEG4/AC3 MKV
conversion, throttled transfer before EOF, Docker entrypoint and preview-only fetch.
19 browser regression tests passed including a 20-minute total that stays fixed
while the playlist grows from 8 to 30 seconds. One actual H.264 browser decode
check was skipped because this local browser build lacks H.264/AAC codecs.
Deployment build and JavaScript/Python syntax checks passed.
Production Telegram/browser playback is not yet verified for this update.

LIMITS
This improves the current progressive pipeline, but does not create persistent
pre-encoded storage/CDN. Temporary streams regenerate after Render restarts.
Cold starts, Telegram throughput and unsupported codecs can still cause waits.
Seeking beyond generated segments must wait. Free server capacity is not a
promise of smooth playback for many concurrent viewers. Durable prepared media
and greater capacity require separate hosting/storage configuration.
