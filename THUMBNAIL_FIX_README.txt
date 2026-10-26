TamilCartoons playback + thumbnail update

1. Supabase > SQL Editor: run sql/04_fix_sample_episode.sql.
   The observed live Episode 1 still points to a sample channel/message.
   The guarded UPDATE changes only that sample row to the previously supplied
   real video: https://t.me/c/4309976850/19. No other episode is changed.

2. Replace these existing GitHub files using the same paths:
   player.html
   assets/js/common.js
   assets/js/anime.js
   assets/js/player.js
   assets/js/config.js
   assets/css/app.css
   telegram-backend/stream_server.py
   Keep all other project files. Upload the extracted FILES, not the ZIP.
   The ZIP's assets/ and telegram-backend/ folders belong at repository root.

3. Wait for GitHub Pages and Render deployments to finish. Render should
   auto-deploy after the backend commit; otherwise use Manual Deploy.
   Then refresh with Ctrl+Shift+R.

Result: real Telegram media thumbnails on both anime and player episode
lists, and selected video thumbnail as player poster. No database thumbnail
column is needed. Telegram files without a stored thumbnail display
'Preview unavailable'; the backend does not generate frames or transcode.

Live diagnosis (26 Oct 2026):
- Current sample Episode 1 request: 403, channel not in TG_ALLOWED_CHANNELS.
- Actual channel -1004309976850, message 19: 206, video/mp4, byte range 0-511
  returned correctly; size 110787463 bytes. The initial bytes identify MP4
  with H.264 data. ffprobe confirms H.264 video and AAC audio. Full browser playback was not verified.
- Database SQL and production changes have NOT been applied by this bundle.

Implementation: allowlisted, bounded thumbnail downloads (up to 1 MiB,
4 concurrent downloads, 30s timeout). Downloads only Telegram thumbnail
file IDs, never the full video to obtain a preview. Missing previews keep
an honest placeholder. A HEAD probe reports disallowed/sample episode
links before attempting video playback.

Reference layout: centered large player, purple selected state, season buttons
and compact episode thumbnail grid (8 desktop / 3 mobile columns). Changing
a season changes the list; the current video keeps playing until an episode
card is selected. Previous/next follows the currently playing season.
