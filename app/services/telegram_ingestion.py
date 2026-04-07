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
        
        from app.services import db
        try:
            db_settings = db.get_settings()
            db_chats = db_settings.get("monitored_chats", "")
        except:
            db_chats = ""
            
        env_chats = os.getenv("TELEGRAM_TARGET_CHAT") or os.getenv("TELEGRAM_CHANNEL") or ""
        combined = f"{db_chats},{env_chats}"
        self.target_chat_names = list(set([c.strip() for c in combined.split(",") if c.strip()]))
        
        self.client = None
        self.monitored_ids = set()
        self.monitored_names = {} # {id: name}
        self.topic_cache = {}    # {chat_id: {topic_id: topic_name}}
        self.me_id = None

        # Mapeo de Nombres y IDs para consistencia con Dashboard
        self.id_to_name = {}
        # Primero procesamos los nombres (prioridad estética para el Dashboard)
        # Luego los IDs (para asegurar captura si el nombre cambia)
        for entry in self.target_chat_names:
            clean = entry.strip()
            if not (clean.startswith("-") or clean.isdigit()):
                # Es un nombre - lo guardaremos para buscarlo por nombre después
                pass
            else:
                try:
                    cid = int(clean)
                    self.monitored_ids.add(cid)
                    # Solo lo ponemos si no hay ya un nombre mejor (pero aquí aún no iteramos dialogs)
                except: pass

    async def start(self):
        if not self.api_id or not self.api_hash:
            logger.error("[Telegram] Faltan credenciales en el .env")
            return

        logger.info(f"[Telegram] Conectando para {self.phone}...")
        self.client = TelegramClient('trading_session', int(self.api_id), self.api_hash)
        await self.client.start(phone=self.phone)
        
        # 1. Identificar 'ME'
        me = await self.client.get_me()
        self.me_id = me.id
        self.monitored_ids.add(self.me_id)
        self.id_to_name[self.me_id] = "Mensajes Guardados (ME)"

        # 2. Descubrir Grupos y mapear IDs con prioridad al nombre configurado
        async for dialog in self.client.iter_dialogs(archived=True):
            d_name = dialog.name
            d_id = dialog.id
            
            for target in self.target_chat_names:
                clean_target = target.strip()
                # Si el nombre coincide, ganamos la etiqueta legible
                if d_name.lower() == clean_target.lower():
                    self.monitored_ids.add(d_id)
                    # IMPORTANTE: Si ya teníamos un ID aquí, el nombre TIENE PRIORIDAD
                    self.id_to_name[d_id] = clean_target 
                    logger.info(f"[Telegram] Vinculado: '{d_name}' => '{clean_target}'")
                
                # Si el ID coincide, solo lo ponemos si no hay nombre ya asignado
                elif str(d_id) == clean_target:
                    self.monitored_ids.add(d_id)
                    if d_id not in self.id_to_name:
                        self.id_to_name[d_id] = clean_target
                        logger.info(f"[Telegram] Vinculado por ID: {d_id}")

        # 4. HANDLER UNIVERSAL
        @self.client.on(events.NewMessage())
        async def universal_handler(event):
            if not event.raw_text: return
            
            chat_id = event.chat_id
            topic_id = None
            
            # Si el mensaje tiene un reply_to, verificamos si es un tema (Forum Topic)
            if event.message.reply_to:
                # El top_id es el identificador del tema en Telethon
                topic_id = getattr(event.message.reply_to, 'reply_to_top_id', None)
            
            # Identificador unificado para hilos o chats simples
            lookup_id = f"{chat_id}_{topic_id}" if topic_id else chat_id
            
            # Verificación de monitoreo (probamos el ID de tema primero, luego el de chat)
            is_monitored = lookup_id in self.monitored_ids or chat_id in self.monitored_ids
            
            # Obtener nombre para el log
            raw_source = self.id_to_name.get(lookup_id) or self.id_to_name.get(chat_id, str(chat_id))
            
            if is_monitored:
                try:
                    raw_text = event.raw_text
                    # Obtenemos la etiqueta EXACTA (Priorizamos el Tema si existe)
                    source = raw_source.strip()
                    
                    logger.info(f"[Telegram] CAPTURA de '{source}': {raw_text[:40]}...")
                    
                    # El motor guardará el log con este 'source'
                    await self.engine.process_signal(raw_text, source=source)
                    
                except Exception as e:
                    logger.error(f"[Telegram] Error en procesamiento: {e}")
            else:
                # Log a nivel INFO para que el usuario sepa que llegó algo y por qué se ignora
                logger.info(f"[Telegram] IGNORADO: Mensaje de '{raw_source}' (ID: {chat_id}) - No está en Monitoreo.")

        logger.info(f"[Telegram] ESCUCHA ACTIVA. Etiquetas configuradas: {list(self.id_to_name.values())}")
        
        # Sincronización PROFUNDA al iniciar para cargar chats guardados en DB
        from app.services import db
        db_settings = db.get_settings()
        saved_chats = db_settings.get("monitored_chats", "")
        if saved_chats:
            logger.info(f"[Telegram] Sincronizando chats persistentes: {saved_chats}")
            await self.refresh_monitored_chats(saved_chats)

        await self.client.run_until_disconnected()

    async def get_all_dialogs(self):
        """
        Escanea todos los chats accesibles para el usuario con soporte para Temas (Communities).
        """
        if not self.client or not await self.client.is_user_authorized():
            logger.error("[Telegram] Cliente no autorizado.")
            return []
            
        dialog_list = []
        try:
            logger.info("[Telegram] Iniciando escaneo profundo (Dialogs + Topics)...")
            from telethon.tl.types import Channel, Chat
            from telethon.tl.functions.channels import GetForumTopicsRequest
            
            async for dialog in self.client.iter_dialogs(limit=None):
                d_type = "Usuario"
                is_forum = False
                
                if isinstance(dialog.entity, Channel):
                    d_type = "Canal"
                    if getattr(dialog.entity, 'forum', False):
                        is_forum = True
                        d_type = "Comunidad"
                    elif getattr(dialog.entity, 'megagroup', False):
                        d_type = "Grupo"
                elif isinstance(dialog.entity, Chat):
                    d_type = "Grupo"
                
                if hasattr(dialog.entity, 'bot') and dialog.entity.bot:
                    d_type = "Bot"
                
                # Agregar el diálogo principal
                dialog_list.append({
                    "id": dialog.id,
                    "name": dialog.name or "Sin Nombre",
                    "type": d_type,
                    "unread": dialog.unread_count,
                    "is_monitored": dialog.id in self.monitored_ids
                })

                # Si es un Foro (Comunidad), extraer sus temas (Topics)
                if is_forum:
                    try:
                        # Obtenemos los temas recientes del foro
                        topics = await self.client(GetForumTopicsRequest(
                            channel=dialog.entity,
                            offset_date=None,
                            offset_id=0,
                            offset_topic=0,
                            limit=100
                        ))
                        from telethon.tl.types import ForumTopic
                        for topic in topics.topics:
                            if not isinstance(topic, ForumTopic):
                                continue # Ignorar temas borrados o nulos
                                
                            topic_id = f"{dialog.id}_{topic.id}" # ID compuesto para identificar el tema
                            dialog_list.append({
                                "id": topic_id,
                                "name": f"{dialog.name} > {topic.title}",
                                "type": "Tema",
                                "unread": 0,
                                "is_monitored": topic_id in self.monitored_ids
                            })
                    except Exception as te:
                        logger.warning(f"[Telegram] Error al obtener temas de {dialog.name}: {te}")
            
            # 3. COMPENSACIÓN: Intentar buscar chats configurados que NO se encontraron en los diálogos
            found_names = set(self.id_to_name.values())
            for target in self.target_chat_names:
                if not target: continue
                if target.strip() not in found_names:
                    try:
                        # Intento de búsqueda global razonable
                        entity = await self.client.get_entity(target.strip())
                        d_id = entity.id
                        d_name = (getattr(entity, 'title', "") or getattr(entity, 'first_name', "") or target).strip()
                        self.monitored_ids.add(d_id)
                        self.id_to_name[d_id] = target.strip()
                        logger.info(f"[Telegram] VINCULO FORZADO (Búsqueda Directa): '{d_name}' (ID: {d_id})")
                    except Exception as ex:
                        logger.debug(f"[Telegram] No se pudo encontrar '{target}' mediante búsqueda directa: {ex}")

            logger.info(f"[Telegram] Escaneo completado. Se han detectado {len(dialog_list)} ítems.")
            return dialog_list
        except Exception as e:
            logger.error(f"[Telegram] Error crítico al listar diálogos: {e}")
            return []

    async def refresh_monitored_chats(self, new_chat_list_str):
        """
        Actualiza la lista de chats monitoreados en 'caliente', incluyendo soporte para Temas.
        """
        self.target_chat_names = [c.strip() for c in new_chat_list_str.split(",") if c.strip()]
        self.monitored_ids = {self.me_id} if hasattr(self, 'me_id') else set()
        self.id_to_name = {self.me_id: "Mensajes Guardados (ME)"} if hasattr(self, 'me_id') else {}
        
        from telethon.tl.functions.channels import GetForumTopicsRequest
        from telethon.tl.types import Channel

        async for dialog in self.client.iter_dialogs(limit=None):
            d_name = (dialog.name or "Sin Nombre").strip()
            d_id = dialog.id
            entity = dialog.entity
            
            # Fix para evitar NoneType error si el username es None
            raw_username = getattr(entity, 'username', "") or ""
            d_username = raw_username.lower() if entity else ""
            
            # Log de auditoría silencioso en consola
            logger.info(f"[Telegram] Detectado: '{d_name}' (ID: {d_id}, @{d_username})")

            # 1. Verificar si el diálogo principal coincide
            for target in self.target_chat_names:
                if not target: continue
                clean_target = target.strip().lower()
                clean_target_no_at = clean_target.replace("@", "")
                
                # Match por Nombre exacto, Nombre minúsculas, ID o Username
                matches = (
                    d_name.lower() == clean_target or
                    str(d_id) == clean_target or
                    d_username == clean_target or
                    d_username == clean_target_no_at
                )
                
                if matches:
                    # Guardamos ambos formatos (string e int) para evitar problemas de tipo en el handler
                    self.monitored_ids.add(d_id)
                    self.monitored_ids.add(str(d_id))
                    self.id_to_name[d_id] = target.strip()
                    self.id_to_name[str(d_id)] = target.strip()
                    logger.info(f"[Telegram] Vinculado con éxito: '{d_name}' (@{d_username})")
            
            # 2. Si es un Foro, buscar coincidencias en sus temas
            if isinstance(entity, Channel) and getattr(entity, 'forum', False):
                try:
                    topics = await self.client(GetForumTopicsRequest(
                        channel=entity, offset_date=None, offset_id=0, offset_topic=0, limit=50
                    ))
                    for topic in topics.topics:
                        topic_name = f"{d_name} > {topic.title}"
                        topic_id = f"{d_id}_{topic.id}"
                        
                        for target in self.target_chat_names:
                            if topic_name.lower() == target.lower() or topic_id == target:
                                self.monitored_ids.add(topic_id)
                                self.id_to_name[topic_id] = target
                except Exception as e:
                    logger.debug(f"[Telegram] Silencio en topics de {d_name}: {e}")
        
        logger.info(f"[Telegram] Lista de monitoreo actualizada: {list(self.id_to_name.values())}")

    async def get_discoverable_chats(self):
        if not self.client or not self.client.is_connected(): return []
        discovery = []
        async for dialog in self.client.iter_dialogs(archived=True, limit=100):
            entity = dialog.entity
            chat_info = {
                "id": dialog.id, "name": dialog.name,
                "type": type(entity).__name__, "is_forum": getattr(entity, "forum", False), "topics": []
            }
            if chat_info["is_forum"]:
                try:
                    res = await self.client(functions.channels.GetForumTopicsRequest(
                        channel=entity, offset_date=None, offset_id=0, offset_topic=0, limit=50
                    ))
                    for t in res.topics:
                        if hasattr(t, "title"): chat_info["topics"].append({"id": t.id, "title": t.title})
                except: pass
            discovery.append(chat_info)
        return discovery
