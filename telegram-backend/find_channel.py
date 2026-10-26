"""Private diagnostic; lists accessible channels without changing content."""
import asyncio
import os
from dotenv import load_dotenv
from pyrogram import Client

async def main():
    load_dotenv()
    async with Client('diagnostic', api_id=int(os.environ['TG_API_ID']), api_hash=os.environ['TG_API_HASH'], session_string=os.environ['TG_SESSION_STRING'], in_memory=True) as app:
        async for dialog in app.get_dialogs():
            print(dialog.chat.id, dialog.chat.title or '(private chat)')

if __name__ == '__main__':
    asyncio.run(main())
