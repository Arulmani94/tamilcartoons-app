TAMILCARTOONS V10 — RAIN LOADING, NO PLAYER POSTER

INSTALL
1. Extract this ZIP. Replace/upload all website files using exactly the folder paths in this ZIP. Do NOT delete other repository files. Keep your config.js, backend environment variables and existing requirements.txt.
2. Commit changes in GitHub. This time the BACKEND CHANGES ARE REQUIRED: telegram-backend/Dockerfile and telegram-backend/stream_server.py.
3. Render must deploy the new commit. The Dockerfile installs FFmpeg. If auto-deploy does not start, use Render > service > Manual Deploy > Deploy latest commit. Wait for success and Telegram ready.
4. Wait for GitHub Pages deployment, then refresh the website (Ctrl+Shift+R on desktop).
No Supabase SQL changes are required. No new private credentials are required.

BEHAVIOR
- Home catalogue photos display in 16:9 landscape cards.
- Shinchan cutout is the header logo and favicon. Loading now uses a transparent umbrella-Shinchan sprite inspired by your supplied GIF. CSS rain covers the whole video viewport. Download progress is shown as text; rain and the character animate while preparing/buffering. The original GIF is not edited frame-for-frame; this is a newly generated four-frame version of the umbrella character.
- Normal MP4 files play directly. Actual container bytes are checked, rather than trusting .mp4 names or Telegram MIME labels.
- MKV, MPEG-TS and other supported FFmpeg containers are prepared as MP4 before playback. H.264/yuv420p video is copied when possible; incompatible video is converted to H.264. Non-AAC audio becomes AAC. Conversion selects the first non-cover video and first audio track, and omits embedded subtitles/data tracks.
- Prepared MP4 supports HTTP byte ranges for seek, reverse/forward and browser duration. Existing purple theme, mobile layout, double-tap seek, swipe fullscreen, thumbnail/post-photo fallback and bulk-import fixes are included.

PRACTICAL LIMITS
First preparation downloads the full source and may take several minutes. One file is prepared at a time; other viewers wait. Converting unsupported codecs can take longer on Render Free. Source/output limit defaults to 1 GiB per file (MEDIA_MAX_MB=1024); the temporary cache is bounded. Large or damaged/encrypted/DRM files can fail and show an error. The cache is temporary and files may need preparation again after eviction/restart. This is support for common video containers/codecs, not a guarantee for every arbitrary file. Rendering a browser's native fullscreen notification cannot be suppressed by the site.

DIAGNOSIS & VALIDATION
The live Shinchan Episode 1 (Telegram message 2) returned video/mp4 but FFprobe identified MPEG-TS with H.264/AAC. A bounded 2 MiB sample from that exact video was successfully repackaged into genuine H.264/AAC MP4 locally. The complete 299,611,190-byte episode was not downloaded or production-converted during this task.
48 checks passed for the integrated site/backend, followed by 31 backend checks after extending document MIME acceptance (49 distinct checks total). These include real MKV/TS remuxing, incompatible MP4 codec conversion, prepared-byte ranges, authorization, incomplete download errors, frontend preparation/loading, landscape home cards, gestures, poster fallback and bulk imports. Actual Render deployment and physical mobile hardware remain unverified until you upload.

IMAGE ASSETS
Built-in image_gen was used. Asset paths: assets/img/shinchan-loading.png and assets/img/shinchan-run-sheet.png. Prompts: transparent Shinchan-only mascot based on the supplied character reference; then a consistent four-frame 2x2 running-in-place sprite sheet, with no background/dog/envelope/text, for CSS frame animation. Original generated alpha channels were preserved. No API key is needed for these finished image files.

REFERENCE DOCUMENTATION
https://www.ffmpeg.org/ffmpeg-formats.html
https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Containers

V10 CHANGE: Video player has NO thumbnail/poster, even before Play. Episode cards BELOW/BESIDE the player retain Telegram thumbnails and post-photo fallback. Rain/character appears only while loading and disappears when ready. The app header logo remains the Shinchan logo from V9.
V10 validation: 18 frontend checks passed, including no-player-poster, preserved episode previews, full-player rain bounds and loader hidden after preparation. Backend unchanged from V9.
