import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def list_chats():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")

    if not api_id or not api_hash:
        print("Faltan credenciales en el .env")
        return

    client = TelegramClient('trading_session', int(api_id), api_hash)
    await client.start(phone=phone)
    
    print("\n--- LISTA DE CHATS DETECTADOS POR TELEGRAM ---")
    print("ID | NOMBRE")
    print("-" * 30)
    
    async for dialog in client.iter_dialogs():
        print(f"{dialog.id} | {dialog.name}")
    
    await client.disconnect()
    print("\n--- FIN DE LA LISTA ---")

if __name__ == "__main__":
    asyncio.run(list_chats())
