TAMILCARTOONS — PURPLE MOBILE V8

Extract this ZIP. Replace these SEVEN existing files in GitHub, keeping paths:
index.html
anime.html
player.html
assets/css/app.css
assets/js/common.js
assets/js/anime.js
assets/js/player.js

Commit changes, wait for GitHub Pages deployment, then refresh. No SQL or Render changes needed. Keep other files, including admin.html, config.js and the Telegram backend. Upload the extracted files, not the ZIP.

Changes:
- Full-width 16:9 inline video on mobile, as marked in the reference screenshot.
- Purple styling on homepage, detail page and player.
- Horizontal scrollable season buttons on anime detail and player pages.
- Mobile episodes are three thumbnail cards per row, with normal downward page scrolling. Desktop player keeps the episode sidebar.
- Telegram video thumbnails are attempted first. If unavailable or broken, cards use the anime post poster_url; the player poster also falls back to that image. If both images fail, the existing missing-preview placeholder remains. No endless fallback requests.
- Existing swipe fullscreen, rotated portrait fallback, double-tap seek, inline buffering and transparent playback controls retained.
- Versioned CSS/JS links reduce stale cache conflicts.

Validation: 13 browser checks passed, including real local-media playback/seek, gestures, mobile layout, image-error fallback and broken fallback handling. Actual phone hardware and production deployment were not tested/applied by this ZIP.
