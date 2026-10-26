PLAYER V7 — SKY BLUE

Replace exactly these GitHub files, keeping paths:
player.html
assets/js/player.js
assets/css/app.css

Commit, wait for GitHub Pages deploy, then refresh. Download/extract this newest ZIP; do not upload the ZIP itself. No Supabase SQL or Render changes are needed.

Changes:
- Sky blue player accents.
- Transparent center Play/Pause, with 10-second reverse/forward on either side.
- Double tap left/right part of the video to seek -10/+10 seconds.
- Single tap background toggles controls; use Play/Pause button to pause.
- Buffering indicator and loading message are INSIDE the video, not below its title.
- Swipe up or tap Fullscreen to expand. Requests native fullscreen and orientation lock. If portrait orientation remains on a narrow screen, rotates the player and controls into landscape inside fullscreen/viewport fallback. Original video ratio is preserved without stretching.
- Existing episode sidebar and navigation retained.

Browser fullscreen origin/exit notifications are controlled by the browser, not this website. Actual mobile hardware is not available for testing; synthetic touch and mobile viewport checks pass, along with actual local-video seek/play tests (11 browser checks).
