"""Browser integration tests with a fake Supabase and health service; no live accounts."""
import functools
import http.server
import threading
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[2]
STUB=r'''
window.supabase = {createClient: () => {
 const anime=Array.from({length:26},(_,i)=>({id:String(i+1),name:i===0?'Hero Adventure':'Series '+(i+1),description:'A story of adventure.',storyline:'Discover a new world.',poster_url:'',created_at:'2026-10-01',category:i%2?'Tamil':'Tamil Dubbed Anime',genre:'Adventure',studio:'Studio',rating:8,status:'Ongoing',is_trending:i<2}));
 const tables={anime,seasons:[{id:'s1',anime_id:'1',season_number:1,season_name:'Season One'},{id:'s2',anime_id:'1',season_number:2,season_name:'Season Two'}],episodes:[{id:'e1',season_id:'s1',episode_number:1,telegram_channel_id:'-1001234567890',telegram_message_id:1},{id:'e2',season_id:'s1',episode_number:2,telegram_channel_id:'-1001234567890',telegram_message_id:2},{id:'e3',season_id:'s2',episode_number:1,telegram_channel_id:'-1001234567890',telegram_message_id:3}]};
 return {auth:{getSession:async()=>({data:{session:{user:{email:'test@example.com'}}},error:null}),signOut:async()=>({error:null}),onAuthStateChange:()=>{},signInWithPassword:async()=>({data:{user:{email:'test@example.com'}},error:null})},rpc:async()=>({data:!location.search.includes('deny'),error:null}),from:(name)=>{
 let rows=[...(tables[name]||[])],single=false,cols='*';const q={select:(c)=>{cols=c;return q},eq:(k,v)=>{rows=rows.filter(r=>String(r[k])===String(v));return q},ilike:(k,v)=>{rows=rows.filter(r=>String(r[k]).toLowerCase().includes(v.replaceAll('%','').toLowerCase()));return q},order:()=>q,range:(a,b)=>{rows=rows.slice(a,b+1);return q},limit:n=>{rows=rows.slice(0,n);return q},single:()=>{single=true;return q},then:(resolve)=>resolve(location.search.includes('legacy')&&/category|is_trending/.test(cols)?{data:null,error:{message:'column category does not exist',code:'42703'}}:{data:single?rows[0]:rows,error:null})};return q;
 }};
}};
'''

@pytest.fixture(scope='module')
def browser_env():
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        yield browser,f'http://127.0.0.1:{server.server_port}'
        browser.close()
    server.shutdown()

@pytest.fixture
def page(browser_env):
    browser,base=browser_env
    context=browser.new_context(viewport={'width':390,'height':844})
    context.route('**/cdn.jsdelivr.net/**',lambda route:route.fulfill(body=STUB,content_type='application/javascript'))
    context.route('**/assets/js/config.js',lambda route:route.fulfill(body="window.TC_CONFIG={supabaseUrl:'https://db.example',supabaseKey:'public',backendUrl:'https://stream.example'}",content_type='application/javascript'))
    context.route('https://stream.example/health',lambda route:route.fulfill(json={'telegram_ready':True},headers={'Access-Control-Allow-Origin':'*'}))
    context.route('https://stream.example/video**',lambda route:route.fulfill(status=404,body='mock no media',headers={'Access-Control-Allow-Origin':'*'}))
    page=context.new_page();page.base=base
    yield page
    context.close()

def test_home_search_category_pagination(page):
    page.goto(page.base+'/index.html')
    expect(page.locator('#grid .card')).to_have_count(24)
    page.locator('#more').click();expect(page.locator('#grid .card')).to_have_count(26)
    expect(page.locator('#more')).to_be_hidden()
    page.get_by_role('button',name='Tamil',exact=True).click()
    expect(page.locator('#grid .card')).to_have_count(13)
    page.get_by_role('button',name='All titles',exact=True).click()
    page.locator('#search').fill('Hero');page.get_by_role('button',name='Search',exact=True).click()
    expect(page.locator('#grid .card')).to_have_count(1)
    page.locator('#grid .card').click();expect(page).to_have_url(page.base+'/anime.html?id=1')
    expect(page.locator('#seasons option')).to_have_count(2)
    expect(page.locator('#episodes a')).to_have_count(2)
    page.locator('#seasons').select_option('s2');expect(page.locator('#episodes a')).to_have_count(1)
    expect(page.locator('#episodes a')).to_have_attribute('href','player.html?episode_id=e3')
    page.locator('#seasons').select_option('s1');expect(page.locator('#episodes a')).to_have_count(2)
    page.locator('#episodes a').first.click()
    expect(page.locator('#title')).to_have_text('Hero Adventure')
    expect(page.locator('#prev')).to_be_disabled();expect(page.locator('#next')).to_be_enabled()
    expect(page.locator('#video')).to_have_attribute('src','https://stream.example/video?channel_id=-1001234567890&message_id=1')
    page.locator('#fullscreen').click()
    page.wait_for_function("document.fullscreenElement?.id === 'watchStage'")
    expect(page.locator('#customControls')).to_be_visible()
    page.locator('#fullscreen').click()
    page.locator('#next').click();expect(page.locator('#meta')).to_contain_text('Episode 2')
    expect(page.locator('#next')).to_be_disabled();expect(page.locator('#prev')).to_be_enabled()
    page.locator('#prev').click();expect(page.locator('#meta')).to_contain_text('Episode 1')
    assert page.locator('iframe,input[type=file],#audioSelect').count()==0
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')

def test_legacy_schema_and_empty_search(page):
    page.goto(page.base+'/index.html?legacy=1')
    expect(page.locator('#grid .card')).to_have_count(24)
    page.get_by_role('button',name='Tamil',exact=True).click()
    expect(page.locator('#grid')).to_contain_text('metadata migration')
    page.get_by_role('button',name='All titles',exact=True).click()
    page.locator('#search').fill('nothing matches');page.get_by_role('button',name='Search',exact=True).click()
    expect(page.locator('#grid')).to_contain_text('No matches')

def test_admin_preserved_and_authorization(page):
    page.goto(page.base+'/admin.html?deny=1')
    expect(page.locator('#appScreen')).to_be_hidden()
    expect(page.locator('#loginStatus')).to_contain_text('not an authorized administrator')
    page.goto(page.base+'/admin.html')
    expect(page.locator('#appScreen')).to_be_visible()
    page.locator('[data-page=episodes]').click()
    page.locator('#episodeAnime').select_option('1');page.locator('#episodeSeason').select_option('s1')
    page.locator('#telegramLinks').fill('https://t.me/c/1234567890/19\nhttps://t.me/example/20')
    page.locator('#previewLinksBtn').click()
    expect(page.locator('#linkPreview')).to_contain_text('Episode 3')
    expect(page.locator('#linkPreview')).to_contain_text('Episode 4')
    page.locator('[data-page=saved]').click()
    expect(page.locator('#savedList')).to_be_visible()

def test_missing_episode_and_backend(page):
    page.goto(page.base+'/player.html')
    expect(page.locator('#playbackError')).to_contain_text('No episode selected')
    page.route('**/assets/js/config.js',lambda route:route.fulfill(body="window.TC_CONFIG={supabaseUrl:'https://db.example',supabaseKey:'public',backendUrl:''}",content_type='application/javascript'))
    page.goto(page.base+'/player.html?episode_id=e1')
    expect(page.locator('#playbackError')).to_contain_text('actual Render HTTPS')
    expect(page.locator('#next')).to_be_enabled()

def test_desktop_and_mobile_layout(page, tmp_path):
    for width in [390,1440]:
        page.set_viewport_size({'width':width,'height':900})
        page.goto(page.base+'/index.html');expect(page.locator('#grid .card')).to_have_count(24)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if width==1440: page.screenshot(path=str(tmp_path/'home_desktop.png'),full_page=True)
        page.goto(page.base+'/anime.html?id=1');expect(page.locator('#episodes a')).to_have_count(2)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
