"""Bounded-memory Telegram byte streaming. One Uvicorn worker per session."""
import asyncio
import logging
import mimetypes
import os
import re
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

load_dotenv()
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
log = logging.getLogger('tamilcartoons')
CHUNK_SIZE = 1024 * 1024  # Pyrogram stream_media offsets count 1 MiB chunks.


def channel_value(value):
    value = str(value).strip()
    if re.fullmatch(r'-100[1-9]\d{0,12}', value):
        return int(value)
    if re.fullmatch(r'@[A-Za-z][A-Za-z0-9_]{3,31}', value):
        return value.lower()
    raise ValueError('Use a -100 channel ID or @channel_username')


def parse_range(header, size):
    if size <= 0:
        raise ValueError('Empty media')
    if header is None:
        return 0, size - 1, 200
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', header.strip())
    if not match or not any(match.groups()):
        raise ValueError('Only one bytes range is supported')
    first, last = match.groups()
    if first:
        start = int(first)
        end = min(int(last), size - 1) if last else size - 1
    else:
        suffix = int(last)
        if suffix <= 0:
            raise ValueError('Invalid suffix')
        start, end = max(0, size - suffix), size - 1
    if start >= size or start > end:
        raise ValueError('Unsatisfiable range')
    return start, end, 206


async def media_bytes(client, message, start, end, request):
    first_chunk, last_chunk = start // CHUNK_SIZE, end // CHUNK_SIZE
    remaining, skip = end - start + 1, start % CHUNK_SIZE
    iterator = client.stream_media(message, offset=first_chunk, limit=last_chunk - first_chunk + 1)
    try:
        async for chunk in iterator:
            if await request.is_disconnected():
                return
            if skip:
                chunk, skip = chunk[skip:], 0
            chunk = chunk[:remaining]
            if chunk:
                remaining -= len(chunk)
                yield chunk
            if remaining <= 0:
                return
        if remaining:
            log.error('Telegram stream ended early; missing_bytes=%s', remaining)
            raise RuntimeError('Incomplete Telegram stream')
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        log.error('Telegram streaming failed: %s', type(exc).__name__)
        raise
    finally:
        if hasattr(iterator, 'aclose'):
            await iterator.aclose()


@asynccontextmanager
async def lifespan(app):
    app.state.telegram = None
    app.state.ready = False
    # No interactive login is ever started by the web service.
    try:
        api_id = int(os.environ['TG_API_ID'])
        api_hash = os.environ['TG_API_HASH']
        session = os.environ['TG_SESSION_STRING'].strip()
        allowed = {channel_value(x) for x in os.environ['TG_ALLOWED_CHANNELS'].split(',') if x.strip()}
        if not api_hash or not session or not allowed:
            raise ValueError('Missing Telegram configuration')
        client = Client('tamilcartoons', api_id=api_id, api_hash=api_hash,
                        session_string=session, in_memory=True, no_updates=True,
                        sleep_threshold=0)
        app.state.allowed = allowed
        app.state.telegram = client
        authorized = await asyncio.wait_for(client.connect(), timeout=30)
        if not authorized:
            raise RuntimeError('Session is not authorized')
        await asyncio.wait_for(client.initialize(), timeout=30)
        await asyncio.wait_for(client.get_me(), timeout=30)
        # Resolve numeric peers once after every in-memory session restart.
        async def resolve_peers():
            async for dialog in client.get_dialogs():
                if dialog.chat.id in allowed:
                    log.info('Configured channel peer resolved')
        await asyncio.wait_for(resolve_peers(), timeout=60)
        app.state.ready = True
        log.info('Telegram authorized; streaming ready')
    except Exception as exc:
        log.error('Telegram startup failed (%s). Check private environment/session/access.', type(exc).__name__)
    try:
        yield
    finally:
        client = app.state.telegram
        if client:
            if client.is_initialized:
                await client.terminate()
            if client.is_connected:
                await client.disconnect()
        app.state.ready = False


app = FastAPI(title='TamilCartoons streaming', lifespan=lifespan)
origins = [x.strip() for x in os.getenv('FRONTEND_ORIGINS', 'https://arulmani94.github.io').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'HEAD'],
                   allow_headers=['Range'], expose_headers=['Content-Range', 'Accept-Ranges', 'Content-Length'],
                   allow_credentials=False)


@app.get('/')
async def root():
    return {'service': 'TamilCartoons', 'health': '/health'}


@app.get('/health')
async def health():
    client = getattr(app.state, 'telegram', None)
    ready = bool(getattr(app.state, 'ready', False) and client and client.is_connected)
    return JSONResponse({'status': 'ok' if ready else 'not_ready', 'telegram_ready': ready},
                        status_code=200 if ready else 503)


@app.api_route('/video', methods=['GET', 'HEAD'])
async def video(request: Request, channel_id: str = Query(..., max_length=40),
                message_id: int = Query(..., ge=1, le=2147483647)):
    try:
        channel = channel_value(channel_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    # CORS is not authentication. Allowlist also blocks non-browser requests to other chats.
    if channel not in getattr(app.state, 'allowed', set()):
        raise HTTPException(403, 'Channel is not in TG_ALLOWED_CHANNELS')
    client = getattr(app.state, 'telegram', None)
    if not getattr(app.state, 'ready', False) or not client or not client.is_connected:
        raise HTTPException(503, 'Telegram is not ready; check server configuration')
    try:
        message = await asyncio.wait_for(client.get_messages(channel, message_id), timeout=30)
    except FloodWait as exc:
        raise HTTPException(429, 'Telegram rate limit; retry later', headers={'Retry-After': str(exc.value)})
    except asyncio.TimeoutError:
        raise HTTPException(504, 'Telegram metadata request timed out')
    except RPCError as exc:
        log.warning('Telegram lookup failed: %s', type(exc).__name__)
        raise HTTPException(404, 'Message unavailable or session cannot access channel')
    media = (getattr(message, 'video', None) or getattr(message, 'document', None)) if message else None
    if not media or not media.file_size:
        raise HTTPException(404, 'Message has no media file')
    size = media.file_size
    mime = getattr(media, 'mime_type', None) or mimetypes.guess_type(getattr(media, 'file_name', '') or '')[0] or 'application/octet-stream'
    if not (mime.startswith('video/') or mime == 'application/octet-stream'):
        raise HTTPException(415, 'Message is not a video document')
    try:
        start, end, code = parse_range(request.headers.get('range'), size)
    except ValueError:
        raise HTTPException(416, 'Invalid byte range', headers={'Content-Range': f'bytes */{size}'})
    headers = {'Accept-Ranges': 'bytes', 'Content-Length': str(end - start + 1),
               'Content-Type': mime, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
    if code == 206:
        headers['Content-Range'] = f'bytes {start}-{end}/{size}'
    log.info('media request method=%s message=%s status=%s bytes=%s-%s', request.method, message_id, code, start, end)
    if request.method == 'HEAD':
        return Response(status_code=code, headers=headers)
    return StreamingResponse(media_bytes(client, message, start, end, request), status_code=code, headers=headers)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '10000')), workers=1, access_log=False)
