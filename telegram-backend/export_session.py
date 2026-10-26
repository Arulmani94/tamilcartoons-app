"""Run privately in Termux or trusted computer. Never run as a public web endpoint."""
import asyncio
import getpass
import os
from pathlib import Path
from dotenv import load_dotenv
from pyrogram import Client

async def main():
    load_dotenv()
    api_id = int(os.getenv('TG_API_ID') or input('Telegram API ID: '))
    api_hash = os.getenv('TG_API_HASH') or getpass.getpass('Telegram API hash (hidden): ')
    # Optional existing session base path: omit .session; stop other clients first.
    existing = input('Existing session path WITHOUT .session, or Enter for new login: ').strip()
    app = Client(existing or 'private_setup', api_id=api_id, api_hash=api_hash, in_memory=not bool(existing))
    async with app:
        value = await app.export_session_string()
        path = Path('private_session_string.txt')
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(value)
        print('Saved private_session_string.txt. Copy its content ONLY into Render TG_SESSION_STRING, then delete it.')

if __name__ == '__main__':
    asyncio.run(main())
