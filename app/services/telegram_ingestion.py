import os
import asyncio
from telethon import TelegramClient, events, functions, types
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

class TelegramService:
    def __init__(self, engine):
        self.engine = engine
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.phone = os.getenv("TELEGRAM_PHONE")
        
        # Obtener chats de la DB y del .env
        from app.services import db
        try:
            db_settings = db.get_settings()
            db_chats = db_settings.get("monitored_chats", "")
        except:
            db_chats = ""
            
        env_chats = os.getenv("TELEGRAM_TARGET_CHAT") or os.getenv("TELEGRAM_CHANNEL") or ""
        
        combined = f"{db_chats},{env_chats}"
        self.target_chat_names = list(set([c.strip() for c in combined.split(",") if c.strip()]))
        
        if not self.target_chat_names:
            self.target_chat_names = ["RETO 1k a 10k"]
            
        self.client = None
        self.topic_cache = {} # {chat_id: {topic_id: topic_name}}

    async def start(self):
        """
        Inicia el cliente de Telegram y busca los chats objetivos.
        """
        if not self.api_id or not self.api_hash:
            logger.error("[Telegram] Faltan credenciales (API_ID/HASH) en el archivo .env")
            return

        logger.info(f"[Telegram] Iniciando sesión para {self.phone}...")
        self.client = TelegramClient('trading_session', int(self.api_id), self.api_hash)
        
        await self.client.start(phone=self.phone)
        logger.info("[Telegram] Cliente autenticado correctamente.")

        # Buscar los IDs de los chats por nombre (ahora case-insensitive y en archivados)
        target_entities = []
        async for dialog in self.client.iter_dialogs(archived=True):
            dialog_name_lower = dialog.name.lower()
            
            # Verificamos si el nombre del diálogo coincide con algún chat objetivo
            matching_name = next((name for name in self.target_chat_names if name.lower() == dialog_name_lower), None)
            
            if matching_name:
                target_entities.append(dialog)
                logger.info(f"[Telegram] Chat monitoreado activo: {dialog.name} (ID: {dialog.id})")
                
                # Si es un foro, cachear los temas (Topics)
                if getattr(dialog.entity, 'forum', False):
                    self.topic_cache[dialog.id] = {}
                    try:
                        topics_res = await self.client(functions.channels.GetForumTopicsRequest(
                            channel=dialog.entity,
                            offset_date=None, offset_id=0, offset_topic=0, limit=100
                        ))
                        for topic in topics_res.topics:
                            if hasattr(topic, 'title'):
                                self.topic_cache[dialog.id][topic.id] = topic.title
                        logger.info(f"   |-- Temas cargados para {dialog.name}: {len(self.topic_cache[dialog.id])}")
                    except Exception as e:
                        logger.warning(f"   |-- No se pudieron cargar temas para {dialog.name}: {e}")

        # --- LOGICA DE DESCUBRIMIENTO DE TEMAS SI EL USUARIO PUSO EL NOMBRE DEL TEMA ---
        # Si algún chat no se encontró como Diálogo, buscamos si es un Tema en algún foro visible
        found_names = [e.name.lower() for e in target_entities]
        missing_names = [name for name in self.target_chat_names if name.lower() not in found_names]
        
        if missing_names:
            logger.info(f"[Telegram] Buscando {len(missing_names)} fuentes faltantes en los temas de comunidades...")
            async for dialog in self.client.iter_dialogs(archived=True):
                if getattr(dialog.entity, 'forum', False):
                    try:
                        topics_res = await self.client(functions.channels.GetForumTopicsRequest(
                            channel=dialog.entity,
                            offset_date=None, offset_id=0, offset_topic=0, limit=100
                        ))
                        for topic in topics_res.topics:
                            if hasattr(topic, 'title') and topic.title.lower() in [m.lower() for m in missing_names]:
                                # Añadimos el diálogo padre si no estaba ya
                                if dialog not in target_entities:
                                    target_entities.append(dialog)
                                # Aseguramos que el tema esté en el caché
                                if dialog.id not in self.topic_cache: self.topic_cache[dialog.id] = {}
                                self.topic_cache[dialog.id][topic.id] = topic.title
                                logger.info(f"[Telegram] ¡Tema detectado! '{topic.title}' en la comunidad '{dialog.name}'")
                    except: pass
        
        if not target_entities:
            logger.warning(f"[Telegram] No se encontró ninguno de los chats en {self.target_chat_names}. Escuchando globalmente.")

        # Handler para cada chat encontrado
        for entity in target_entities:
            @self.client.on(events.NewMessage(chats=entity.id))
            async def handler(event, chat_name=entity.name, chat_id=entity.id):
                raw_text = event.raw_text
                
                # Detectar si el mensaje viene de un Tema (Topic)
                topic_name = None
                if event.message.reply_to:
                    reply_to = event.message.reply_to
                    # En foros, el top_msg_id suele ser el ID del tema
                    topic_id = getattr(reply_to, 'reply_to_top_id', None) or getattr(reply_to, 'reply_to_msg_id', None)
                    if topic_id and chat_id in self.topic_cache:
                        topic_name = self.topic_cache[chat_id].get(topic_id)
                
                source = f"{chat_name} -> {topic_name}" if topic_name else chat_name
                
                logger.info(f"[Telegram][{source}] Mensaje capturado.")
                # Delegamos el procesamiento al motor con la fuente detallada
                await self.engine.process_signal(raw_text, source=source)

        logger.info(f"[Telegram] Escuchando en {len(target_entities)} fuentes: {', '.join([e.name for e in target_entities])}")
        await self.client.run_until_disconnected()

    async def get_discoverable_chats(self):
        """
        Retorna una lista de todos los chats, canales y temas accesibles para el usuario.
        Útil para el panel de descubrimiento del Dashboard.
        """
        if not self.client or not self.client.is_connected():
            return []
            
        discovery = []
        async for dialog in self.client.iter_dialogs(archived=True, limit=100):
            entity = dialog.entity
            chat_info = {
                "id": dialog.id,
                "name": dialog.name,
                "type": type(entity).__name__,
                "is_forum": getattr(entity, "forum", False),
                "topics": []
            }
            
            if chat_info["is_forum"]:
                try:
                    res = await self.client(functions.channels.GetForumTopicsRequest(
                        channel=entity, offset_date=None, offset_id=0, offset_topic=0, limit=50
                    ))
                    for t in res.topics:
                        if hasattr(t, "title"):
                            chat_info["topics"].append({"id": t.id, "title": t.title})
                except: pass
                
            discovery.append(chat_info)
            
        return discovery
