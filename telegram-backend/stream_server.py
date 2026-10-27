"""Bounded-memory Telegram byte streaming. One Uvicorn worker per session."""
import asyncio
import secrets
from urllib.parse import urlencode
import logging
import json
import shutil
import tempfile
import time
from pathlib import Path
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
        tasks = [j['task'] for j in hls_jobs.values() if not j.get('finished')]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
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


def authorized_client(channel_id):
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
    return client, channel


async def lookup_media(channel_id, message_id):
    client, channel = authorized_client(channel_id)
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
    return client, message, media


thumbnail_slots = asyncio.Semaphore(4)


@app.get('/thumbnail')
async def thumbnail(channel_id: str = Query(..., max_length=40),
                    message_id: int = Query(..., ge=1, le=2147483647)):
    client, message, media = await lookup_media(channel_id, message_id)
    thumbs = [t for t in (getattr(media, 'thumbs', None) or [])
              if 0 < (getattr(t, 'file_size', 0) or 0) <= 1024 * 1024]
    if not thumbs:
        raise HTTPException(404, 'This video has no Telegram thumbnail')
    thumb = max(thumbs, key=lambda t: getattr(t, 'width', 0) * getattr(t, 'height', 0))
    try:
        async with thumbnail_slots:
            file = await asyncio.wait_for(client.download_media(thumb.file_id, in_memory=True), timeout=30)
        if file is None:
            raise HTTPException(404, 'Thumbnail unavailable')
        try:
            data = file.read(1024 * 1024 + 1)
        finally:
            file.close()
        if not data or len(data) > 1024 * 1024:
            raise HTTPException(502, 'Invalid thumbnail')
        return Response(data, media_type='image/jpeg', headers={'Cache-Control': 'private, max-age=3600', 'X-Content-Type-Options': 'nosniff'})
    except FloodWait as exc:
        raise HTTPException(429, 'Telegram rate limit', headers={'Retry-After': str(exc.value)})
    except asyncio.TimeoutError:
        raise HTTPException(504, 'Thumbnail request timed out')
    except RPCError:
        raise HTTPException(404, 'Thumbnail unavailable')


@app.api_route('/video', methods=['GET', 'HEAD'])
async def video(request: Request, channel_id: str = Query(..., max_length=40),
                message_id: int = Query(..., ge=1, le=2147483647)):
    client, message, media = await lookup_media(channel_id, message_id)
    size = media.file_size
    mime = getattr(media, 'mime_type', None) or mimetypes.guess_type(getattr(media, 'file_name', '') or '')[0] or 'application/octet-stream'
    extension = Path(getattr(media, 'file_name', '') or '').suffix.lower()
    known_video = extension in {'.mp4', '.mkv', '.mov', '.avi', '.ts', '.m2ts', '.m4v', '.webm', '.wmv', '.mpeg', '.mpg', '.flv', '.3gp', '.vob', '.rm', '.rmvb'}
    if not (mime.startswith('video/') or mime in {'application/octet-stream', 'application/x-matroska', 'application/mp4', 'application/mpeg'} or known_video):
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


# One conversion at a time; temporary files are bounded and discarded on restart.
PREP_ROOT = Path(tempfile.mkdtemp(prefix='tc-media-'))
PREP_MAX = int(os.getenv('MEDIA_MAX_MB', '1024')) * 1024 * 1024
PREP_FORMATS = 'mov,matroska,webm,mpegts,mpeg,mpegvideo,avi,flv,ogg,asf,m4v,hevc,h264,mjpeg,rm'
prepared = {}
prepare_lock = asyncio.Lock()

async def media_command(*args, timeout=60):
    process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    try:
        output, _ = await asyncio.wait_for(process.communicate(), timeout)
        if process.returncode:
            raise RuntimeError('Media processing failed; file may be damaged or encrypted')
        return output
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()

async def probe_file(path):
    data = await media_command('ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe',
        '-format_whitelist', PREP_FORMATS, '-show_streams', '-show_format', '-of', 'json', str(path))
    return json.loads(data)

def conversion_args(info, source, target):
    videos = [s for s in info.get('streams', []) if s.get('codec_type') == 'video' and not s.get('disposition', {}).get('attached_pic')]
    audio = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
    if not videos:
        raise RuntimeError('No playable video track in this Telegram file')
    v = videos[0]
    copy_video = v.get('codec_name') == 'h264' and v.get('pix_fmt') in ('yuv420p', 'yuvj420p')
    args = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-threads', '1', '-protocol_whitelist', 'file,pipe',
        '-format_whitelist', PREP_FORMATS, '-i', str(source), '-map', '0:' + str(v['index']), '-map', '0:a:0?', '-sn', '-dn']
    args += ['-c:v', 'copy'] if copy_video else ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', '-vf', 'scale=w=min(1280\\,iw):h=min(720\\,ih):force_original_aspect_ratio=decrease:force_divisible_by=2', '-threads', '1']
    args += ['-c:a', 'copy'] if not audio or audio[0].get('codec_name') == 'aac' else ['-c:a', 'aac', '-b:a', '128k']
    args += ['-movflags', '+faststart', '-fs', str(PREP_MAX), str(target)]
    return args, copy_video

async def prepare_file(client, message, media, job):
    source, target = job['source'], job['target']
    try:
        async def download():
            written = 0
            async for chunk in client.stream_media(message):
                written += len(chunk)
                if written > PREP_MAX or written > media.file_size:
                    raise RuntimeError('Source video exceeds preparation limit')
                with source.open('ab') as file:
                    file.write(chunk)
                job['progress'] = min(99, int(written * 100 / media.file_size))
            if written != media.file_size:
                raise RuntimeError('Telegram download incomplete; try again later')
        await asyncio.wait_for(download(), 900)
        job['state'] = 'inspecting'
        info = await probe_file(source)
        args, copy_video = conversion_args(info, source, target)
        job['state'] = 'remuxing' if copy_video else 'transcoding'
        await media_command(*args, timeout=1800)
        check = await probe_file(target)
        before = float(info.get('format', {}).get('duration') or 0)
        after = float(check.get('format', {}).get('duration') or 0)
        if not target.exists() or target.stat().st_size >= PREP_MAX or (before and after < before - 2):
            raise RuntimeError('Prepared video incomplete or exceeds limit')
        job['state'], job['progress'] = 'ready', 100
    except Exception as exc:
        job['state'] = 'error'
        job['error'] = str(exc) if isinstance(exc, RuntimeError) else 'Video preparation failed or timed out; check Render logs'
        target.unlink(missing_ok=True)
        log.warning('Video preparation failed: %s', type(exc).__name__)
    finally:
        source.unlink(missing_ok=True)
        job['updated'] = time.monotonic()

@app.get('/media-info')
async def media_info(channel_id: str = Query(..., max_length=40), message_id: int = Query(..., ge=1, le=2147483647)):
    authorized_client(channel_id)
    existing = hls_jobs.get((str(channel_value(channel_id)), message_id))
    if existing and existing['state'] != 'error':
        return {'needs_preparation': True, 'detected': 'hls_available'}
    client, message, media = await lookup_media(channel_id, message_id)
    stream = client.stream_media(message, offset=0, limit=1)
    try:
        first = await asyncio.wait_for(anext(stream), 30)
    except (StopAsyncIteration, asyncio.TimeoutError):
        raise HTTPException(504, 'Could not inspect video bytes')
    finally:
        await stream.aclose()
    # Trust actual container bytes rather than Telegram MIME or filename.
    mp4 = len(first) >= 12 and first[4:8] == b'ftyp'
    return {'needs_preparation': not mp4, 'detected': 'mp4' if mp4 else 'requires_mp4_conversion',
            'mime': getattr(media, 'mime_type', None), 'size': media.file_size}

@app.get('/prepare')
async def prepare(channel_id: str = Query(..., max_length=40), message_id: int = Query(..., ge=1, le=2147483647), retry_failed: bool = False):
    client, message, media = await lookup_media(channel_id, message_id)
    key = (str(channel_value(channel_id)), message_id)
    async with prepare_lock:
        job = prepared.get(key)
        if job and job['state'] == 'error' and retry_failed:
            job['target'].unlink(missing_ok=True)
            prepared.pop(key)
            job = None
        if job:
            return {k: job[k] for k in ('state', 'progress', 'error') if k in job}
        if any(j['state'] not in ('ready', 'error') for j in prepared.values()) or any(not j.get('finished') for j in hls_jobs.values()):
            return JSONResponse({'state': 'busy', 'detail': 'Another video is being prepared. Waiting…'}, status_code=202)
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            raise HTTPException(503, 'Deploy updated Dockerfile with FFmpeg before using compatibility playback')
        if media.file_size > PREP_MAX:
            raise HTTPException(413, 'File exceeds preparation size limit; convert it to H.264/AAC MP4 before uploading')
        # Bound the completed cache as well as each source/output. Telegram originals are unchanged.
        for old_key, old in list(prepared.items()):
            if time.monotonic() - old['updated'] > 3600 or shutil.disk_usage(PREP_ROOT).free < media.file_size * 2 + 128 * 1024 * 1024:
                old['target'].unlink(missing_ok=True)
                prepared.pop(old_key)
        while prepared and sum(j['target'].stat().st_size for j in prepared.values() if j['target'].exists()) + media.file_size * 2 > 1536 * 1024 * 1024:
            oldest = min(prepared, key=lambda k: prepared[k]['updated'])
            prepared.pop(oldest)['target'].unlink(missing_ok=True)
        if len(prepared) >= 8:
            old_key = min(prepared, key=lambda k: prepared[k]['updated'])
            prepared.pop(old_key)['target'].unlink(missing_ok=True)
        if shutil.disk_usage(PREP_ROOT).free < media.file_size * 2 + 128 * 1024 * 1024:
            raise HTTPException(507, 'Not enough temporary storage to prepare this video')
        folder = Path(tempfile.mkdtemp(dir=PREP_ROOT))
        job = {'state': 'downloading', 'progress': 0, 'source': folder / 'source.media', 'target': folder / 'ready.mp4', 'updated': time.monotonic()}
        prepared[key] = job
        job['task'] = asyncio.create_task(prepare_file(client, message, media, job))
        return {'state': 'downloading', 'progress': 0}

@app.api_route('/prepared-video', methods=['GET', 'HEAD'])
async def prepared_video(request: Request, channel_id: str = Query(..., max_length=40), message_id: int = Query(..., ge=1, le=2147483647)):
    await lookup_media(channel_id, message_id)
    job = prepared.get((str(channel_value(channel_id)), message_id))
    if not job or job['state'] != 'ready' or not job['target'].exists():
        raise HTTPException(409, 'Video is not prepared yet; retry playback to prepare it')
    job['updated'] = time.monotonic()
    try:
        size = job['target'].stat().st_size
        start, end, code = parse_range(request.headers.get('range'), size)
    except ValueError:
        raise HTTPException(416, 'Invalid byte range', headers={'Content-Range': f'bytes */{size}'})
    headers = {'Content-Length': str(end - start + 1), 'Content-Type': 'video/mp4', 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-store'}
    if code == 206:
        headers['Content-Range'] = f'bytes {start}-{end}/{size}'
    if request.method == 'HEAD':
        return Response(status_code=code, headers=headers)
    # Open before yielding so cache eviction cannot remove an actively streamed file on Linux.
    file = job['target'].open('rb')
    async def body():
        try:
            file.seek(start)
            remaining = end - start + 1
            while remaining and not await request.is_disconnected():
                chunk = file.read(min(256 * 1024, remaining))
                if not chunk: break
                remaining -= len(chunk)
                yield chunk
                await asyncio.sleep(0)
        finally:
            file.close()
    return StreamingResponse(body(), status_code=code, headers=headers)



# Progressive HLS: publish each completed segment while Telegram is still feeding
# FFmpeg. Originals never need to be saved in full before playback starts.
hls_jobs = {}
hls_lock = asyncio.Lock()
HLS_ROOT = Path(tempfile.mkdtemp(prefix='tc-hls-'))


def hls_args(source, folder):
    return ['ffmpeg', '-v', 'error', '-nostdin', '-y',
            '-protocol_whitelist', 'http,tcp', '-rw_timeout', '30000000',
            '-probesize', '2097152', '-analyzeduration', '2000000', '-format_whitelist', PREP_FORMATS, '-i', source,
            '-map', '0:v:0', '-map', '0:a:0?', '-sn', '-dn',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '25',
            '-threads', '1', '-maxrate', '2000k', '-bufsize', '4000k', '-pix_fmt', 'yuv420p',
            '-vf', "scale=w='min(1280,iw)':h='min(720,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2",
            '-force_key_frames', 'expr:gte(t,n_forced*2)',
            '-c:a', 'aac', '-b:a', '128k', '-f', 'hls', '-hls_time', '2',
            '-hls_playlist_type', 'event', '-hls_flags', 'independent_segments+temp_file',
            '-hls_segment_filename', str(folder / 'seg%06d.ts'), str(folder / 'index.m3u8')]


async def run_hls(job, source):
    process = None
    try:
        process = await asyncio.create_subprocess_exec(*hls_args(source, job['folder']),
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        job['process'] = process
        deadline = time.monotonic() + 7200
        while process.returncode is None:
            if time.monotonic() > deadline:
                raise RuntimeError('Streaming time limit reached')
            if sum(p.stat().st_size for p in job['folder'].iterdir() if p.is_file()) > PREP_MAX:
                raise RuntimeError('Streaming cache limit reached')
            if shutil.disk_usage(HLS_ROOT).free < 128 * 1024 * 1024:
                raise RuntimeError('Video server storage is full')
            if (job['folder'] / 'index.m3u8').exists():
                job['state'] = 'ready'
            await asyncio.sleep(.5)
        if process.returncode or not (job['folder'] / 'index.m3u8').exists():
            raise RuntimeError('This video could not be streamed. Check its source or upload an H.264/AAC MP4.')
        job['state'] = 'ready'
    except Exception as exc:
        job['state'], job['error'] = 'error', str(exc) if isinstance(exc, RuntimeError) else 'Streaming failed; retry later'
    finally:
        if process and process.returncode is None:
            process.kill()
            await process.wait()
        job['finished'] = True
        job['updated'] = time.monotonic()


@app.get('/start-stream')
async def start_stream(channel_id: str = Query(..., max_length=40),
                       message_id: int = Query(..., ge=1, le=2147483647), retry: bool = False):
    authorized_client(channel_id)
    key = (str(channel_value(channel_id)), message_id)
    async with hls_lock:
        job = hls_jobs.get(key)
        if job and job['state'] == 'error' and retry:
            shutil.rmtree(job['folder'], ignore_errors=True)
            del hls_jobs[key]
            job = None
        if job is None:
            await lookup_media(channel_id, message_id)
            # Completed unused jobs expire. Never evict a job actively encoding.
            for oldkey, old in list(hls_jobs.items()):
                if old.get('finished') and time.monotonic() - old['updated'] > 3600:
                    shutil.rmtree(old['folder'], ignore_errors=True)
                    del hls_jobs[oldkey]
            if any(not j.get('finished') for j in hls_jobs.values()) or any(j['state'] not in ('ready', 'error') for j in prepared.values()):
                return JSONResponse({'state': 'busy'}, status_code=202)
            used = sum(p.stat().st_size for p in HLS_ROOT.rglob('*') if p.is_file())
            if used > 512 * 1024 * 1024 or len(hls_jobs) >= 4:
                raise HTTPException(503, 'Streaming cache is busy; retry later')
            if not shutil.which('ffmpeg'):
                raise HTTPException(503, 'Deploy Dockerfile with FFmpeg')
            token = secrets.token_hex(16)
            folder = HLS_ROOT / token
            folder.mkdir()
            job = {'token': token, 'folder': folder, 'state': 'starting', 'finished': False, 'updated': time.monotonic(), 'key': key}
            hls_jobs[key] = job
            source = 'http://127.0.0.1:' + os.getenv('PORT', '10000') + '/video?' + urlencode({'channel_id': key[0], 'message_id': message_id})
            job['task'] = asyncio.create_task(run_hls(job, source))
        job['updated'] = time.monotonic()
        return {k: job[k] for k in ('state', 'token', 'error') if k in job}


@app.get('/hls/{token}/{filename}')
async def hls_file(token: str, filename: str):
    if not re.fullmatch(r'[0-9a-f]{32}', token) or not re.fullmatch(r'index\.m3u8|seg[0-9]{6}\.ts', filename):
        raise HTTPException(404, 'Stream unavailable')
    job = next((j for j in hls_jobs.values() if j['token'] == token), None)
    if not job:
        raise HTTPException(404, 'Stream expired; reload episode')
    authorized_client(job['key'][0])
    path = job['folder'] / filename
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise HTTPException(404, 'Segment not ready')
    job['updated'] = time.monotonic()
    return Response(data, media_type='application/vnd.apple.mpegurl' if filename.endswith('.m3u8') else 'video/mp2t',
                    headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '10000')), workers=1, access_log=False)
