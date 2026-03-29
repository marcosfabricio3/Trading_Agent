from app.logger import logger
import asyncio

class TradeMonitor:
    """
    Monitor activo de trades.
    Encargado de: 
    1. Seguir el precio de posiciones abiertas en DB.
    2. Ejecutar cierres parciales en TP1.
    3. Mover SL a Break-Even tras TP1.
    """
    def __init__(self, engine, exchange, db):
        self.engine = engine
        self.exchange = exchange
        self.db = db
        self.active_monitors = {} # {symbol: trade_info}

    async def run(self, interval=2):
        """
        Bucle de monitoreo infinito.
        """
        logger.info("[Monitor] Ciclo de monitoreo activo iniciado.")
        while True:
            try:
                # 1. Obtener trades abiertos
                active_trades = self.db.get_active_trades()
                
                if active_trades:
                    logger.debug(f"[Monitor] Analizando {len(active_trades)} trades activos...")
                
                # 2. Verificar cada trade
                for trade in active_trades:
                    market_data = self.exchange.get_market_price(trade["symbol"])
                    current_price = market_data["price"]
                    self.check_targets(trade, current_price)
                
            except Exception as e:
                logger.error(f"[Monitor] Error en el ciclo: {e}")
            
            await asyncio.sleep(interval)

    def check_targets(self, trade, current_price):
        """
        Lógica para TP1 y Break-Even.
        """
        side = trade["side"].lower()
        if side == "long":
            if current_price >= trade["tp"] and not trade["tp1_hit"]:
                self.handle_tp1(trade)
            elif current_price <= trade["sl"]:
                self.handle_exit(trade, current_price, "Stop Loss")
        
        elif side == "short":
            if current_price <= trade["tp"] and not trade["tp1_hit"]:
                self.handle_tp1(trade)
            elif current_price >= trade["sl"]:
                self.handle_exit(trade, current_price, "Stop Loss")

    def handle_tp1(self, trade):
        """
        TP1 Alcanzado: Cerrar 50% y mover SL a Entrada.
        """
        logger.info(f"🎯 [Monitor] TP1 Alcanzado para {trade['symbol']} ({trade['tp']})")
        
        # 1. Cierre parcial en Bitget
        self.exchange.close_position_partial(trade["symbol"], 0.5)
        
        # 2. Mover SL a Break-Even en Bitget
        self.exchange.update_sl(trade["symbol"], trade["entry_price"])
        
        # 3. Actualizar estado en DB (usamos 'details' para campos extra)
        details = {"tp1_hit": True, "sl_moved": True}
        self.db.update_trade_status(trade["id"], "active", details=details)
        
        logger.info(f"🛡️ [Monitor] {trade['symbol']}: Parcial cerrado y SL movido a Entrada ({trade['entry_price']})")

    def handle_exit(self, trade, price, reason):
        """
        Cierre total del trade.
        """
        logger.info(f"🚩 [Monitor] Exit detectado ({reason}) para {trade['symbol']} a {price}")
        details = {"exit_price": price, "exit_reason": reason}
        self.db.update_trade_status(trade["id"], "closed", details=details)
