import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stream_server import app, parse_range, CHUNK_SIZE

PAYLOAD = bytes(range(256)) * (CHUNK_SIZE // 256 * 3) + b'end'

class Telegram:
    is_connected = True
    def __init__(self):
        self.calls = []
    async def get_messages(self, channel, message):
        if message == 2:
            return SimpleNamespace(video=None, document=None)
        media = SimpleNamespace(file_size=len(PAYLOAD), mime_type='video/mp4', file_name='test.mp4')
        return SimpleNamespace(video=media, document=None)
    async def stream_media(self, message, offset, limit):
        self.calls.append((offset, limit))
        for n in range(offset, offset + limit):
            chunk = PAYLOAD[n * CHUNK_SIZE:(n + 1) * CHUNK_SIZE]
            if chunk:
                yield chunk

@pytest.fixture
def client():
    fake = Telegram()
    app.state.telegram = fake
    app.state.allowed = {-1001234567890, '@example'}
    app.state.ready = True
    # Deliberately do not enter lifespan: no real credentials or Telegram requests.
    return TestClient(app), fake

def url(message=1, channel='-1001234567890'):
    return f'/video?channel_id={channel}&message_id={message}'

@pytest.mark.parametrize('header,start,end,code', [
    (None,0,len(PAYLOAD)-1,200), ('bytes=0-0',0,0,206),
    ('bytes=1048573-1048581',1048573,1048581,206),
    ('bytes=1048583-',1048583,len(PAYLOAD)-1,206),
    ('bytes=-7',len(PAYLOAD)-7,len(PAYLOAD)-1,206),
    ('bytes=0-999999999',0,len(PAYLOAD)-1,206),
    ('bytes=-999999999',0,len(PAYLOAD)-1,206),
])
def test_actual_response_bytes(client,header,start,end,code):
    c, fake = client
    r = c.get(url(), headers={'Range': header} if header else {})
    assert r.status_code == code
    assert r.content == PAYLOAD[start:end+1]
    assert int(r.headers['Content-Length']) == end - start + 1
    assert r.headers['Accept-Ranges'] == 'bytes'
    if code == 206:
        assert r.headers['Content-Range'] == f'bytes {start}-{end}/{len(PAYLOAD)}'
    assert fake.calls[-1] == (start//CHUNK_SIZE,end//CHUNK_SIZE-start//CHUNK_SIZE+1)

@pytest.mark.parametrize('header',['bytes=','bytes=-0','items=0-2','bytes=10-2','bytes=999999999-','bytes=0-1,3-4','bytes=-','bytes=a-b','bytes=+0-2'])
def test_invalid_ranges(client,header):
    c,_ = client
    r=c.get(url(),headers={'Range':header})
    assert r.status_code==416
    assert r.headers['Content-Range']==f'bytes */{len(PAYLOAD)}'

def test_head(client):
    c,fake=client
    r=c.head(url(),headers={'Range':'bytes=10-20'})
    assert r.status_code==206 and not r.content
    assert r.headers['Content-Length']=='11' and not fake.calls

def test_health_ready_and_unready(client):
    c,_=client
    assert c.get('/health').json()['telegram_ready'] is True
    app.state.ready=False
    assert c.get('/health').status_code==503
    assert c.get(url()).status_code==503

def test_validation_and_media(client):
    c,_=client
    assert c.get(url(channel='-100999999')).status_code==403
    assert c.get(url(channel='123')).status_code==422
    assert c.get(url(message=0)).status_code==422
    assert c.get(url(message=2147483648)).status_code==422
    assert c.get(url(message=2)).status_code==404
    assert c.get('/video').status_code==422

def test_cors(client):
    c,_=client
    r=c.get(url(),headers={'Origin':'https://arulmani94.github.io','Range':'bytes=0-2'})
    assert r.headers['access-control-allow-origin']=='https://arulmani94.github.io'
    assert 'content-range' in r.headers['access-control-expose-headers'].lower()
    r=c.get(url(),headers={'Origin':'https://untrusted.example','Range':'bytes=0-2'})
    assert 'access-control-allow-origin' not in r.headers
    r=c.options(url(),headers={'Origin':'https://arulmani94.github.io','Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'range'})
    assert r.status_code==200

def test_channel_username(client):
    c,_=client
    assert c.get(url(channel='@EXAMPLE'),headers={'Range':'bytes=0-1'}).content==PAYLOAD[:2]

def test_disconnect_closes_iterator():
    import asyncio
    from stream_server import media_bytes
    closed=[]
    class Disconnect:
        async def is_disconnected(self): return True
    class Fake:
        async def stream_media(self,*args,**kwargs):
            try: yield b'abc'
            finally: closed.append(True)
    async def run(): return [c async for c in media_bytes(Fake(),None,0,2,Disconnect())]
    assert asyncio.run(run())==[]
    assert closed==[True]

def test_lifespan_missing_env_does_not_prompt(monkeypatch):
    for key in ['TG_API_ID','TG_API_HASH','TG_SESSION_STRING','TG_ALLOWED_CHANNELS']:
        monkeypatch.delenv(key,raising=False)
    with TestClient(app) as c:
        assert c.get('/health').status_code==503
