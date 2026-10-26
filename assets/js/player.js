'use strict';
(async()=>{
 const {$,db,query,episodeColumns,allEpisodes,episodeUrl,esc,telegramIds}=TC;
 const video=$('video');let source='';
 function fail(text){$('playbackError').textContent=text;$('playbackError').hidden=false;$('status').textContent='Playback unavailable';$('retry').hidden=!source;}
 function connect(){if(!source)return;$('playbackError').hidden=true;$('retry').hidden=true;$('status').textContent='Connecting to video server…';video.src=source;video.load();}
 $('retry').addEventListener('click',connect);
 // Native fallback remains usable until custom controls have initialized.
 video.controls=false;$('customControls').hidden=false;$('centerActions').hidden=false;
 async function togglePlay(){try{if(video.paused)await video.play();else video.pause();}catch(e){fail('Could not start playback. Check the connection and media format.');}}
 $('play').addEventListener('click',togglePlay);$('miniPlay').addEventListener('click',togglePlay);
 $('railPrev').addEventListener('click',()=>$('prev').click());$('railNext').addEventListener('click',()=>$('next').click());
 video.addEventListener('click',()=>{if($('watchStage').classList.contains('controls-idle'))showControls();else togglePlay();});
 let idleTimer;
 function showControls(){clearTimeout(idleTimer);$('watchStage').classList.remove('controls-idle');if(!video.paused)idleTimer=setTimeout(()=>{if(!$('watchStage').contains(document.activeElement))$('watchStage').classList.add('controls-idle');},2800);}
 for(const name of ['pointermove','pointerdown','focusin','keydown'])$('watchStage').addEventListener(name,showControls);
 $('watchStage').addEventListener('click',event=>{const button=event.target.closest('button');if(button&&event.detail>0){button.blur();showControls();}});
 video.addEventListener('playing',showControls);video.addEventListener('pause',showControls);video.addEventListener('ended',showControls);
 function skip(seconds){if(!Number.isFinite(video.duration))return;video.currentTime=Math.max(0,Math.min(video.duration,video.currentTime+seconds));}
 $('rewind').addEventListener('click',()=>skip(-10));
 $('forward').addEventListener('click',()=>skip(10));
 video.addEventListener('play',()=>{$('play').innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>';$('play').setAttribute('aria-label','Pause');$('miniPlay').textContent='Ⅱ';$('miniPlay').setAttribute('aria-label','Pause');});video.addEventListener('pause',()=>{$('play').innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';$('play').setAttribute('aria-label','Play');$('miniPlay').textContent='▶';$('miniPlay').setAttribute('aria-label','Play');});
 const clock=s=>Number.isFinite(s)?Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0'):'0:00';
 video.addEventListener('timeupdate',()=>{$('time').textContent=clock(video.currentTime)+' / '+clock(video.duration);$('seek').value=video.duration?video.currentTime/video.duration*100:0;});
 $('seek').addEventListener('input',()=>{if(Number.isFinite(video.duration))video.currentTime=Number($('seek').value)/100*video.duration;});
 $('mute').addEventListener('click',()=>{video.muted=!video.muted;});video.addEventListener('volumechange',()=>{$('mute').textContent=video.muted?'Unmute':'Mute';$('volume').value=video.volume;});
 $('volume').addEventListener('input',()=>{video.volume=Number($('volume').value);});$('speed').addEventListener('change',()=>{video.playbackRate=Number($('speed').value);});
 const stage=$('watchStage');
 function fullscreenActive(){return document.fullscreenElement===stage||document.webkitFullscreenElement===stage||stage.classList.contains('immersive');}
 function syncFullscreen(){const active=fullscreenActive();$('fullscreen').textContent=active?'Exit fullscreen':'Fullscreen';$('fullscreen').setAttribute('aria-pressed',String(active));if(!active){document.body.classList.remove('player-expanded');try{screen.orientation?.unlock?.();}catch{}}showControls();}
 function closeImmersive(){stage.classList.remove('immersive');document.body.classList.remove('player-expanded');syncFullscreen();}
 async function toggleFullscreen(){
  if(stage.classList.contains('immersive')){closeImmersive();return;}
  if(document.fullscreenElement){await document.exitFullscreen();return;}
  if(document.webkitFullscreenElement){document.webkitExitFullscreen();return;}
  try{
   if(stage.requestFullscreen)await stage.requestFullscreen();
   else if(stage.webkitRequestFullscreen)stage.webkitRequestFullscreen();
   else if(video.webkitEnterFullscreen){video.webkitEnterFullscreen();return;}
   else throw new Error('Native fullscreen unavailable');
   try{await screen.orientation?.lock?.('landscape');}catch{/* Rotation depends on browser/device support. */}
  }catch{
   // Viewport fallback keeps playback and custom controls usable on mobile browsers.
   stage.classList.add('immersive');document.body.classList.add('player-expanded');
  }
  syncFullscreen();
 }
 $('fullscreen').addEventListener('click',toggleFullscreen);
 document.addEventListener('fullscreenchange',syncFullscreen);document.addEventListener('webkitfullscreenchange',syncFullscreen);
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&stage.classList.contains('immersive'))closeImmersive();});
 video.addEventListener('webkitendfullscreen',syncFullscreen);
 let swipeStart=null,suppressVideoClickUntil=0;
 stage.addEventListener('touchstart',event=>{
  if(event.touches.length!==1||event.target.closest('button,input,select,label,#customControls')){swipeStart=null;return;}
  const touch=event.touches[0];swipeStart={x:touch.clientX,y:touch.clientY,at:Date.now()};
 },{passive:true});
 stage.addEventListener('touchmove',event=>{
  if(!swipeStart||event.touches.length!==1)return;
  const touch=event.touches[0],dy=swipeStart.y-touch.clientY,dx=Math.abs(touch.clientX-swipeStart.x);
  if(dy>18&&dy>dx*1.3&&event.cancelable)event.preventDefault();
 },{passive:false});
 stage.addEventListener('touchend',event=>{
  const start=swipeStart;swipeStart=null;
  if(!start||event.changedTouches.length!==1)return;
  const touch=event.changedTouches[0],dy=start.y-touch.clientY,dx=Math.abs(touch.clientX-start.x);
  if(dy>=55&&dy>dx*1.3&&Date.now()-start.at<900&&!fullscreenActive()){
   if(event.cancelable)event.preventDefault();suppressVideoClickUntil=Date.now()+700;
   toggleFullscreen().catch(()=>{$('status').textContent='Tap Fullscreen to expand the player.';});
  }
 },{passive:false});
 stage.addEventListener('touchcancel',()=>{swipeStart=null;},{passive:true});
 video.addEventListener('click',event=>{if(Date.now()<suppressVideoClickUntil){event.preventDefault();event.stopImmediatePropagation();}},true);

 video.addEventListener('waiting',()=>{$('status').textContent='Buffering…';});video.addEventListener('stalled',()=>{$('status').textContent='Connection stalled. Waiting for data…';});
 video.addEventListener('loadedmetadata',()=>{$('status').textContent='Ready. Press Play to watch.';});video.addEventListener('playing',()=>{$('status').textContent='Playing';$('playbackError').hidden=true;});video.addEventListener('ended',()=>{$('status').textContent='Episode finished. Choose the next episode.';});
 video.addEventListener('error',()=>{fail('Video playback failed. Check the server connection, Telegram access and browser codec support. MP4 with H.264/AAC is recommended; this backend does not transcode MKV or unsupported codecs.');});
 const id=new URLSearchParams(location.search).get('episode_id');
 if(!id){fail('No episode selected. Open an episode from its anime detail page.');return;}
 try{
  const ep=await query(db().from('episodes').select(episodeColumns).eq('id',id).single());
  const season=await query(db().from('seasons').select('id,anime_id,season_number,season_name').eq('id',ep.season_id).single());
  const anime=await query(db().from('anime').select('id,name,poster_url').eq('id',season.anime_id).single());
  const backdrop=TC.safeImage?TC.safeImage(anime.poster_url):'';
  if(backdrop)document.body.style.setProperty('--watch-backdrop','url('+JSON.stringify(backdrop)+')');
  function watchCard(x,number=season.season_number){const code='S'+String(number).padStart(2,'0')+'E'+String(x.episode_number).padStart(2,'0');return TC.episodeCard(x,ep.id).replace('<span class="episode-label">','<span class="episode-label"><small class="episode-code">'+esc(code)+'</small><br>');}
  $('title').textContent=anime.name;$('meta').textContent=(season.season_name||'Season '+season.season_number)+' · Episode '+ep.episode_number;document.title=anime.name+' · Episode '+ep.episode_number;
  $('back').href='anime.html?id='+encodeURIComponent(anime.id);$('back').textContent='← '+anime.name;
  // Navigation uses authoritative DB ordering, not a caller-supplied list of IDs.
  try{
   const rows=await allEpisodes(season.id);const index=rows.findIndex(x=>String(x.id)===String(ep.id));
   $('episodes').innerHTML=rows.map(x=>watchCard(x)).join('');
   const seasons=await query(db().from('seasons').select('id,season_number,season_name').eq('anime_id',anime.id).order('season_number').order('id'));
   $('seasonTabs').innerHTML=seasons.map(s=>`<button type="button" data-season="${esc(s.id)}" aria-pressed="${String(s.id)===String(season.id)}">${esc(s.season_name||'Season '+s.season_number)}</button>`).join('');
   let seasonVersion=0;
   $('seasonTabs').addEventListener('click',async event=>{
    const button=event.target.closest('button[data-season]');if(!button)return;
    const version=++seasonVersion;
    for(const tab of $('seasonTabs').querySelectorAll('button'))tab.setAttribute('aria-pressed',String(tab===button));
    TC.message('episodes','Loading episodes…');
    try{const episodes=await allEpisodes(button.dataset.season);if(version!==seasonVersion)return;
     $('episodes').innerHTML=episodes.map(x=>watchCard(x,seasons.find(s=>String(s.id)===button.dataset.season)?.season_number||season.season_number)).join('');
     if(!episodes.length)TC.message('episodes','No episodes in this season yet.');
    }catch(e){if(version===seasonVersion)TC.message('episodes',e.message,true);}
   });
   for(const [button,target] of [[$('prev'),index-1],[$('next'),index+1]]){if(index>=0&&target>=0&&target<rows.length){button.disabled=false;$(button.id==='prev'?'railPrev':'railNext').disabled=false;button.addEventListener('click',()=>{location.href=episodeUrl(rows[target].id);});}}
  }catch(e){TC.message('episodes','Could not load episode navigation. '+e.message,true);}
  if(!TC_CONFIG.backendUrl)throw new Error('The administrator must set backendUrl in assets/js/config.js to the actual Render HTTPS service origin.');
  const base=new URL(TC_CONFIG.backendUrl);
  if(base.protocol!=='https:'||base.username||base.password||base.pathname!=='/'||base.search||base.hash)throw new Error('The production backend must be an HTTPS origin without a path.');
  const ids=telegramIds(ep);const url=new URL('/video',base);url.searchParams.set('channel_id',ids.channel);url.searchParams.set('message_id',ids.message);source=url.href;video.poster=TC.thumbnailUrl(ep);
  // A bounded health check distinguishes configuration errors from codec errors.
  $('status').textContent='Checking video server…';
  try{const response=await fetch(new URL('/health',base),{signal:AbortSignal.timeout(75000)});if(!response.ok)throw new Error('Video server is not ready (HTTP '+response.status+'). Check Render logs and Telegram session.');const info=await response.json();if(!info.telegram_ready)throw new Error('Telegram session is not ready.');}
  catch(e){fail(e.name==='TimeoutError'?'The video server took too long to wake up. Retry in a minute.':e.message);return;}
  const probe=await fetch(source,{method:'HEAD',signal:AbortSignal.timeout(45000)});
  if(!probe.ok){
   const reasons={403:'This episode uses a Telegram channel that is not allowed. Edit its Telegram link in Admin; sample links will not play.',404:'The Telegram message has no accessible video. Check the episode link and channel access.',415:'This Telegram message is not a video file.',503:'Telegram is not ready. Check Render logs.'};
   fail(reasons[probe.status]||'Video request failed (HTTP '+probe.status+').');return;
  }
  connect();
 }catch(e){fail(e.message);}
})();
