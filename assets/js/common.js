'use strict';
window.TC = (() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function safeImage(value) { try { const u = new URL(value); return ['https:','http:'].includes(u.protocol) ? u.href : ''; } catch { return ''; } }
  let client;
  function db() {
    if (!window.supabase) throw new Error('Database client could not load. Check your internet connection and refresh.');
    return client ||= window.supabase.createClient(TC_CONFIG.supabaseUrl, TC_CONFIG.supabaseKey);
  }
  async function query(builder) {
    const {data, error} = await builder;
    if (error) throw new Error(error.message + (String(error.code).includes('401') || /key|jwt/i.test(error.message) ? ' Ask the administrator to verify the Supabase publishable key.' : ''));
    return data;
  }
  const animeColumns = 'id,name,description,storyline,poster_url,created_at';
  const episodeColumns = 'id,season_id,episode_number,telegram_channel_id,telegram_message_id,telegram_link,created_at';
  function message(id, text, error = false) { $(id).innerHTML = `<p class="message ${error ? 'error' : ''}" role="status">${esc(text)}</p>`; }
  function poster(a) { const src = safeImage(a.poster_url); return `<div class="poster"><span aria-hidden="true">TC</span>${src ? `<img src="${esc(src)}" alt="${esc(a.name)}" loading="lazy">` : ''}</div>`; }
  function cards(rows) { return rows.map(a => `<a class="card" href="anime.html?id=${encodeURIComponent(a.id)}">${poster(a)}<h3>${esc(a.name)}</h3><small>${esc(a.category || 'Anime & Cartoons')}</small></a>`).join(''); }
  function episodeUrl(id) { return 'player.html?episode_id=' + encodeURIComponent(id); }
  function thumbnailUrl(ep) {
    try { const ids=telegramIds(ep),u=new URL('/thumbnail',TC_CONFIG.backendUrl); if(u.protocol!=='https:')return '';u.searchParams.set('channel_id',ids.channel);u.searchParams.set('message_id',ids.message);return u.href; } catch { return ''; }
  }
  function episodeCard(ep, current, fallbackPoster = '') {
    const fallback=safeImage(fallbackPoster),preview=thumbnailUrl(ep),src=preview||fallback,active=String(ep.id)===String(current);
    return `<a class="episode ${active?'active':''}" href="${episodeUrl(ep.id)}" ${active?'aria-current="page"':''}><div class="episode-thumb"><span class="thumb-placeholder">Preview unavailable</span>${src?`<img src="${esc(src)}" alt="Episode ${esc(ep.episode_number)} preview" ${fallback&&preview&&fallback!==preview?`data-fallback="${esc(fallback)}"`: ''} loading="lazy" decoding="async">`:''}<span class="episode-number">${esc(ep.episode_number)}</span><span class="episode-play" aria-hidden="true">▶</span></div><span class="episode-label">Episode ${esc(ep.episode_number)}</span></a>`;
  }
  async function allEpisodes(seasonId) {
    // Respect PostgREST page limits; deterministic order prevents repeated boundary rows.
    let rows = [];
    for (let offset = 0; ; offset += 500) {
      const batch = await query(db().from('episodes').select(episodeColumns).eq('season_id', seasonId).order('episode_number').order('id').range(offset, offset + 499));
      rows.push(...batch);
      if (batch.length < 500) return rows;
    }
  }
  function telegramIds(ep) {
    let channel = String(ep.telegram_channel_id || '').trim(), message = String(ep.telegram_message_id || '').trim();
    if (!channel || !message) {
      try {
        const u = new URL(/^https?:/i.test(ep.telegram_link) ? ep.telegram_link : 'https://' + ep.telegram_link);
        if (!['t.me','www.t.me','telegram.me','www.telegram.me'].includes(u.hostname)) throw Error();
        const parts = u.pathname.split('/').filter(Boolean);
        if (parts[0] === 'c' && parts.length === 3) { channel = '-100' + parts[1]; message = parts[2]; }
        else if (parts.length === 2 && parts[0] !== 's') { channel = '@' + parts[0]; message = parts[1]; }
      } catch { /* Validation below reports missing identifiers. */ }
    }
    if (!/^(-100[1-9]\d{0,12}|@[A-Za-z][A-Za-z0-9_]{3,31})$/.test(channel) || !/^[1-9]\d*$/.test(message) || Number(message) > 2147483647) throw new Error('This episode has invalid Telegram identifiers. Ask the administrator to edit it.');
    return {channel, message};
  }
  // Hide failed posters without inline event-handler attributes.
  document.addEventListener('error', e => {
    const img=e.target;if(img.tagName!=='IMG')return;
    const fallback=safeImage(img.dataset.fallback);delete img.dataset.fallback;
    if(fallback&&img.src!==fallback){img.hidden=false;img.src=fallback;img.alt='Episode post image';}
    else img.hidden=true;
  }, true);
  function videoPoster(video,ep,fallbackPoster){
    const fallback=safeImage(fallbackPoster),preview=thumbnailUrl(ep);
    if(fallback||preview)video.poster=fallback||preview;
    if(preview){const image=new Image();image.onload=()=>{video.poster=preview;};image.onerror=()=>{if(fallback)video.poster=fallback;};image.src=preview;}
  }

  return {$,esc,safeImage,db,query,animeColumns,episodeColumns,message,poster,cards,episodeUrl,allEpisodes,telegramIds,thumbnailUrl,episodeCard,videoPoster};
})();
