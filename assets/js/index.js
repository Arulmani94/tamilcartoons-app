'use strict';
(() => {
 const {$,db,query,animeColumns,message,cards} = TC;
 let offset = 0, busy = false, generation = 0, search = '', category = '', metadata = true;
 async function load(reset = false) {
  if (reset) { generation++; offset = 0; $('grid').innerHTML = ''; }
  const token = generation;
  if (busy && !reset) return;
  busy = true; $('more').disabled = true; $('more').textContent = 'Loading…';
  if (!offset) message('grid','Loading titles…');
  try {
   let q = db().from('anime').select(metadata ? animeColumns + ',category' : animeColumns).order('created_at',{ascending:false}).order('id',{ascending:false});
   if (category) {
    if (!metadata) { if(token===generation) message('grid','Categories need the metadata migration. The administrator can apply sql/01_metadata.sql.'); return; }
    q = q.eq('category',category);
   }
   if (search) q = q.ilike('name','%' + search + '%');
   const rows = await query(q.range(offset,offset+23));
   if (token !== generation) return;
   if (!offset) $('grid').innerHTML = '';
   $('grid').insertAdjacentHTML('beforeend',cards(rows));
   offset += rows.length; $('count').textContent = offset + ' titles loaded';
   if (!offset) message('grid',search ? 'No matches. Try another title.' : 'No titles in this collection yet.');
   $('more').hidden = rows.length < 24;
  } catch(e) {
   if (token !== generation) return;
   if (metadata && /category|schema cache/i.test(e.message)) { metadata = false; busy = false; return load(true); }
   if (!offset) message('grid','Could not load the collection. ' + e.message,true);
   else $('count').textContent = 'Could not load more. ' + e.message;
   $('more').hidden = false;
  } finally { if (token === generation) { busy = false; $('more').disabled = false; $('more').textContent = 'Load more titles'; } }
 }
 $('searchForm').addEventListener('submit',e=>{e.preventDefault();search=$('search').value.trim();$('listingTitle').textContent=search?'Search results':category||'Latest Anime & Cartoons';load(true);});
 document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>{
  category=button.dataset.category;document.querySelectorAll('[data-category]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  $('listingTitle').textContent=search?'Search results':category||'Latest Anime & Cartoons';load(true);
 }));
 $('more').addEventListener('click',()=>load());
 async function trending(){
  try { const rows=await query(db().from('anime').select(animeColumns+',category').eq('is_trending',true).order('created_at',{ascending:false}).order('id',{ascending:false}).limit(6));
   $('trending').innerHTML=cards(rows);if(!rows.length)message('trending','Trending titles will appear here when selected by the administrator.');
  } catch(e){message('trending',/is_trending|category|schema cache/i.test(e.message)?'Trending needs the metadata migration. No popularity ranking has been invented.':'Could not load trending titles. '+e.message,true);}
 }
 if(new URLSearchParams(location.search).get('focus')==='search')$('search').focus();
 load(true);trending();
})();
