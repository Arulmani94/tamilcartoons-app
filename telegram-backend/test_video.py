"""Private real-Telegram diagnostic, run explicitly with channel and message arguments."""
import asyncio
import os
import sys
from dotenv import load_dotenv
from pyrogram import Client
from stream_server import channel_value

async def main():
    load_dotenv()
    async with Client('diagnostic', api_id=int(os.environ['TG_API_ID']), api_hash=os.environ['TG_API_HASH'], session_string=os.environ['TG_SESSION_STRING'], in_memory=True) as app:
        async for _ in app.get_dialogs():
            pass
        message = await app.get_messages(channel_value(sys.argv[1]), int(sys.argv[2]))
        media = message.video or message.document
        if not media:
            raise RuntimeError('No media found')
        print('Media size:', media.file_size, 'MIME:', media.mime_type)
        async for chunk in app.stream_media(message, limit=1):
            print('First chunk received:', len(chunk), 'bytes')

if __name__ == '__main__':
    asyncio.run(main())
