'use strict';
(async()=>{
 const {$,db,query,episodeColumns,allEpisodes,episodeUrl,esc,telegramIds}=TC;
 const video=$('video');let source='';
 function fail(text){$('playbackError').textContent=text;$('playbackError').hidden=false;$('status').textContent='Playback unavailable';$('retry').hidden=!source;}
 function connect(){if(!source)return;$('playbackError').hidden=true;$('retry').hidden=true;$('status').textContent='Connecting to video server…';video.src=source;video.load();}
 $('retry').addEventListener('click',connect);
 // Native fallback remains usable until custom controls have initialized.
 video.controls=false;$('customControls').hidden=false;
 $('play').addEventListener('click',async()=>{try{if(video.paused)await video.play();else video.pause();}catch(e){fail('Could not start playback. Check the connection and media format.');}});
 video.addEventListener('play',()=>{$('play').textContent='Pause';});video.addEventListener('pause',()=>{$('play').textContent='Play';});
 const clock=s=>Number.isFinite(s)?Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0'):'0:00';
 video.addEventListener('timeupdate',()=>{$('time').textContent=clock(video.currentTime)+' / '+clock(video.duration);$('seek').value=video.duration?video.currentTime/video.duration*100:0;});
 $('seek').addEventListener('input',()=>{if(Number.isFinite(video.duration))video.currentTime=Number($('seek').value)/100*video.duration;});
 $('mute').addEventListener('click',()=>{video.muted=!video.muted;});video.addEventListener('volumechange',()=>{$('mute').textContent=video.muted?'Unmute':'Mute';$('volume').value=video.volume;});
 $('volume').addEventListener('input',()=>{video.volume=Number($('volume').value);});$('speed').addEventListener('change',()=>{video.playbackRate=Number($('speed').value);});
 $('fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else if($('watchStage').requestFullscreen)await $('watchStage').requestFullscreen();else if(video.webkitEnterFullscreen)video.webkitEnterFullscreen();else $('status').textContent='Fullscreen is unavailable on this browser.';}catch{$('status').textContent='Fullscreen could not open.';}});
 video.addEventListener('waiting',()=>{$('status').textContent='Buffering…';});video.addEventListener('stalled',()=>{$('status').textContent='Connection stalled. Waiting for data…';});
 video.addEventListener('loadedmetadata',()=>{$('status').textContent='Ready. Press Play to watch.';});video.addEventListener('playing',()=>{$('status').textContent='Playing';$('playbackError').hidden=true;});video.addEventListener('ended',()=>{$('status').textContent='Episode finished. Choose the next episode.';});
 video.addEventListener('error',()=>{fail('Video playback failed. Check the server connection, Telegram access and browser codec support. MP4 with H.264/AAC is recommended; this backend does not transcode MKV or unsupported codecs.');});
 const id=new URLSearchParams(location.search).get('episode_id');
 if(!id){fail('No episode selected. Open an episode from its anime detail page.');return;}
 try{
  const ep=await query(db().from('episodes').select(episodeColumns).eq('id',id).single());
  const season=await query(db().from('seasons').select('id,anime_id,season_number,season_name').eq('id',ep.season_id).single());
  const anime=await query(db().from('anime').select('id,name').eq('id',season.anime_id).single());
  $('title').textContent=anime.name;$('meta').textContent=(season.season_name||'Season '+season.season_number)+' · Episode '+ep.episode_number;document.title=anime.name+' · Episode '+ep.episode_number;
  $('back').href='anime.html?id='+encodeURIComponent(anime.id);$('back').textContent='← '+anime.name;
  // Navigation uses authoritative DB ordering, not a caller-supplied list of IDs.
  try{
   const rows=await allEpisodes(season.id);const index=rows.findIndex(x=>String(x.id)===String(ep.id));
   $('episodes').innerHTML=rows.map(x=>`<a class="episode ${String(x.id)===String(ep.id)?'active':''}" href="${episodeUrl(x.id)}" ${String(x.id)===String(ep.id)?'aria-current="page"':''}>▶ Episode ${esc(x.episode_number)}</a>`).join('');
   for(const [button,target] of [[$('prev'),index-1],[$('next'),index+1]]){if(index>=0&&target>=0&&target<rows.length){button.disabled=false;button.addEventListener('click',()=>{location.href=episodeUrl(rows[target].id);});}}
  }catch(e){TC.message('episodes','Could not load episode navigation. '+e.message,true);}
  if(!TC_CONFIG.backendUrl)throw new Error('The administrator must set backendUrl in assets/js/config.js to the actual Render HTTPS service origin.');
  const base=new URL(TC_CONFIG.backendUrl);
  if(base.protocol!=='https:'||base.username||base.password||base.pathname!=='/'||base.search||base.hash)throw new Error('The production backend must be an HTTPS origin without a path.');
  const ids=telegramIds(ep);const url=new URL('/video',base);url.searchParams.set('channel_id',ids.channel);url.searchParams.set('message_id',ids.message);source=url.href;
  // A bounded health check distinguishes configuration errors from codec errors.
  $('status').textContent='Checking video server…';
  try{const response=await fetch(new URL('/health',base),{signal:AbortSignal.timeout(75000)});if(!response.ok)throw new Error('Video server is not ready (HTTP '+response.status+'). Check Render logs and Telegram session.');const info=await response.json();if(!info.telegram_ready)throw new Error('Telegram session is not ready.');}
  catch(e){fail(e.name==='TimeoutError'?'The video server took too long to wake up. Retry in a minute.':e.message);return;}
  connect();
 }catch(e){fail(e.message);}
})();
