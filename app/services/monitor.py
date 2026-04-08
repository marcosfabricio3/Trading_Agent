from app.logger import logger
import asyncio

class TradeMonitor:
    """
    Monitor activo de trades.
    Encargado de: 
    1. Seguir el precio de posiciones abiertas en DB.
    2. Ejecutar cierres parciales en TP1.
    3. Mover SL a Break-Even tras TP1.
    4. Promocionar órdenes LIMIT (pending) a posiciones activas (open).
    5. Sincronizar SL/TP bidireccionalmente con el Exchange.
    """
    def __init__(self, engine, exchange, db):
        self.engine = engine
        self.exchange = exchange
        self.db = db
        self.active_monitors = {} # {symbol: trade_info}

    async def run(self, interval=5):
        """
        Bucle de monitoreo infinito con sincronización bidireccional y lógica de promoción.
        """
        logger.info(f"[Monitor] Ciclo de monitoreo iniciado cada {interval}s.")
        sync_counter = 0
        
        while True:
            try:
                # 1. Obtener trades activos (incluye pending y open)
                all_active = self.db.get_active_trades()
                
                if not all_active:
                    await asyncio.sleep(interval)
                    continue

                sync_counter += 1
                
                # 2. Verificar cada trade
                for trade in all_active:
                    symbol = trade["symbol"]
                    current_status = trade.get("status", "open")
                    
                    # A. Verificar si la posición existe en el exchange
                    pos = await self.exchange.get_position(symbol)
                    has_position = pos.get("size", 0) > 0

                    # Lógica de Promoción: Pendiente (LIMIT) -> Abierto (Position)
                    if current_status == "pending":
                        if has_position:
                            logger.info(f"✨ [Monitor] ¡Orden LIMIT ejecutada para {symbol}! Pasando a estado OPEN.")
                            self.db.update_trade_status(trade["id"], status="open")
                            # La procesamos como abierta en el siguiente paso de este mismo ciclo
                            current_status = "open"
                        else:
                            # Sigue esperando precio, no procesamos targets
                            continue

                    # B. Si no hay posición y el estado era open, se cerró el trade externamente
                    if current_status == "open" and not has_position:
                        logger.info(f"💨 [Monitor] {symbol} ya no tiene posición activa. Cerrando en DB.")
                        await self.handle_exit(trade, 0, "External/Manual Close")
                        continue

                    # C. Lógica de Targets y SL (solo para posiciones ya abiertas/ejecutadas)
                    if current_status == "open":
                        market_data = await self.exchange.get_market_price(symbol)
                        current_price = market_data.get("price")
                        if current_price:
                            await self.check_targets(trade, current_price)
                    
                        # D. Sincronización Bidireccional (SL/TP) cada ~25s (5 ciclos de 5s)
                        if sync_counter >= 5:
                            plan = await self.exchange.get_plan_orders(symbol)
                            current_sl = plan.get("sl")
                            current_tp = plan.get("tp")
                            
                            db_sl = trade.get("sl")
                            db_tp = trade.get("tp")
                            
                            needs_db_update = False
                            if current_sl and abs(current_sl - db_sl) > 0.0000001:
                                logger.info(f"🔄 [Monitor] Sincronizando SL para {symbol}: {db_sl} -> {current_sl}")
                                needs_db_update = True
                            if current_tp and abs(current_tp - db_tp) > 0.0000001:
                                logger.info(f"🔄 [Monitor] Sincronizando TP para {symbol}: {db_tp} -> {current_tp}")
                                needs_db_update = True
                                
                            if needs_db_update:
                                self.db.update_trade_parameters(trade["id"], sl=current_sl or db_sl, tp=current_tp or db_tp)

                if sync_counter >= 5:
                    sync_counter = 0
                
            except Exception as e:
                logger.error(f"[Monitor] Error en el ciclo: {e}")
            
            await asyncio.sleep(interval)

    async def check_targets(self, trade, current_price):
        """
        Lógica para TP1 y Break-Even.
        """
        side = trade["side"].lower()
        if side == "long":
            if current_price >= trade["tp"] and not trade["tp1_hit"]:
                await self.handle_tp1(trade)
            elif current_price <= trade["sl"]:
                await self.handle_exit(trade, current_price, "Stop Loss")
        
        elif side == "short":
            if current_price <= trade["tp"] and not trade["tp1_hit"]:
                await self.handle_tp1(trade)
            elif current_price >= trade["sl"]:
                await self.handle_exit(trade, current_price, "Stop Loss")

    async def handle_tp1(self, trade):
        """
        TP1 Alcanzado: Cerrar 50% y mover SL a Entrada.
        """
        logger.info(f"🎯 [Monitor] TP1 Alcanzado para {trade['symbol']} ({trade['tp']})")
        
        # 1. Cierre parcial en Bitget
        await self.exchange.close_position_partial(trade["symbol"], 0.5)
        
        # 2. Mover SL a Break-Even en Bitget
        await self.exchange.update_sl(trade["symbol"], trade["entry_price"])
        
        # 3. Actualizar estado en DB
        self.db.update_trade_status(trade["id"], tp1_hit=True, sl_moved=True)
        
        logger.info(f"🛡️ [Monitor] {trade['symbol']}: Parcial cerrado y SL movido a Entrada ({trade['entry_price']})")

    async def handle_exit(self, trade, price, reason):
        """
        Cierre total del trade.
        """
        logger.info(f"🚩 [Monitor] Exit detectado ({reason}) para {trade['symbol']} a {price}")
        self.db.update_trade_status(trade["id"], exit_price=price)
