'use strict';
(async()=>{
 const {$,db,query,message,esc,poster,allEpisodes,episodeUrl} = TC;
 const id=new URLSearchParams(location.search).get('id');let loadVersion=0;
 if(!id){message('detail','No anime selected. Return to the collection.',true);return;}
 message('detail','Loading anime details…');
 try{
  // * reads optional metadata only if it exists; no absent column is queried here.
  const a=await query(db().from('anime').select('*').eq('id',id).single());
  document.title=a.name+' — TamilCartoons';
  const tags=['genre','status','studio','rating','category'].filter(k=>a[k]!==null&&a[k]!==undefined&&a[k]!=='').map(k=>`<span class="tag">${esc(k)}: ${esc(a[k])}</span>`).join('');
  $('detail').innerHTML=poster(a)+`<div><span class="eyebrow">The story awaits</span><h1>${esc(a.name)}</h1><div class="meta">${tags}</div></div><div class="description"><p>${esc(a.storyline||a.description||'No storyline added yet.')}</p></div>`;
  const seasons=await query(db().from('seasons').select('id,anime_id,season_number,season_name,created_at').eq('anime_id',id).order('season_number').order('id'));
  if(!seasons.length){message('episodes','No seasons have been added yet.');return;}
  $('seasons').innerHTML=seasons.map(s=>`<option value="${esc(s.id)}">${esc(s.season_name||'Season '+s.season_number)}</option>`).join('');$('seasons').disabled=false;
  $('animeSeasonTabs').innerHTML=seasons.map(s=>`<button type="button" data-season="${esc(s.id)}" aria-pressed="${String(s.id)===String($('seasons').value)}">${esc(s.season_name||'Season '+s.season_number)}</button>`).join('');
  $('animeSeasonTabs').addEventListener('click',event=>{const button=event.target.closest('button[data-season]');if(!button)return;$('seasons').value=button.dataset.season;loadSeason();});
  async function loadSeason(){
   for(const button of $('animeSeasonTabs').querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.season===$('seasons').value));
   const version=++loadVersion;message('episodes','Loading episodes…');
   try{const rows=await allEpisodes($('seasons').value);if(version!==loadVersion)return;
    $('episodes').innerHTML=rows.map(ep=>TC.episodeCard(ep,null,a.poster_url)).join('');if(!rows.length)message('episodes','No episodes in this season yet.');
   }catch(e){if(version===loadVersion)message('episodes','Could not load episodes. '+e.message,true);}
  }
  $('seasons').addEventListener('change',loadSeason);await loadSeason();
 }catch(e){message('detail','Could not load this anime. '+e.message,true);}
})();
