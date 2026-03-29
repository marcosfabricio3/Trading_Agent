import os
import asyncio
from telethon import TelegramClient, events
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

class TelegramService:
    def __init__(self, engine):
        self.engine = engine
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.phone = os.getenv("TELEGRAM_PHONE")
        self.target_chat_name = os.getenv("TELEGRAM_TARGET_CHAT") or os.getenv("TELEGRAM_CHANNEL") or "RETO 1k a 10k"
        self.client = None

    async def start(self):
        """
        Inicia el cliente de Telegram y busca el chat objetivo.
        """
        if not self.api_id or not self.api_hash:
            logger.error("[Telegram] Faltan credenciales (API_ID/HASH) en el archivo .env")
            return

        logger.info(f"[Telegram] Iniciando sesión para {self.phone}...")
        
        # 'trading_session' guardará tu sesión para no pedir código siempre
        self.client = TelegramClient('trading_session', int(self.api_id), self.api_hash)
        
        await self.client.start(phone=self.phone)
        logger.info("[Telegram] Cliente autenticado correctamente.")

        # Buscar el ID del chat por el nombre
        target_entity = None
        async for dialog in self.client.iter_dialogs():
            if dialog.name == self.target_chat_name:
                target_entity = dialog.id
                logger.info(f"[Telegram] Chat encontrado: {dialog.name} (ID: {target_entity})")
                break
        
        if not target_entity:
            logger.warning(f"[Telegram] No se encontró el chat '{self.target_chat_name}'. Escuchando globalmente.")

        @self.client.on(events.NewMessage(chats=target_entity))
        async def handler(event):
            raw_text = event.raw_text
            logger.info(f"[Telegram] Mensaje capturado: {raw_text[:50]}...")
            # Delegamos el procesamiento al motor
            await self.engine.process_signal(raw_text)

        logger.info(f"[Telegram] Escuchando señales en '{self.target_chat_name}'...")
        await self.client.run_until_disconnected()
