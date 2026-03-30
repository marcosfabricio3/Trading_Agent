from app.logger import logger

class TradingEngine:
    """
    El 'Cerebro' del bot. Orquestador central que sigue el flujo:
    Parse -> Validate -> Risk -> Execution -> DB.
    """
    
    def __init__(self, parser, validator, risk_manager, exchange, db):
        self.parser = parser
        self.validator = validator
        self.risk_manager = risk_manager
        self.exchange = exchange
        self.db = db

    async def process_signal(self, raw_text: str):
        """
        Procesa un mensaje de Telegram (Señal o Gestión) usando el Pipeline de IA.
        """
        logger.info("[Engine] Analizando mensaje entrante...")
        
        # 1. Interpretación (Categoría + Datos)
        interpretation = await self.parser.parse_signal(raw_text)
        category = interpretation.get("category", "DISCARD")
        data = interpretation.get("data", {})

        if category == "DISCARD" or category == "NOISE":
            logger.info(f"  [Ignorado] Motivo: {interpretation.get('reason', 'Ruido detectado')}")
            return

        if category == "ERROR":
            logger.error(f"  [Error] Fallo en interpretación: {interpretation.get('reason')}")
            return

        # 2. Ejecución según Categoría
        if category == "NEW_SIGNAL":
            await self.handle_new_signal(data, raw_text)
        elif category in ["PARTIAL_CLOSE", "MOVE_BE", "CLOSE_FULL"]:
            await self.handle_management_order(category, data)
        else:
            logger.warning(f"  [Alerta] Categoría no soportada: {category}")

    async def handle_new_signal(self, parsed, raw_text):
        """Lógica original de apertura de trades."""
        logger.info(f"  [OK] Nueva señal detectada: {parsed['symbol']} {parsed['side'].lower()}")
        
        # Normalización de Side (AI puede devolver LONG o long)
        side = parsed.get("side", "unknown").lower()
        if side not in ["long", "short"]:
            logger.warning(f"  [Rechazada] Invalid side: {side}")
            return

        # Validación
        validation = self.validator.validate_signal(parsed)
        if not validation["valid"]:
            logger.warning(f"  [Rechazada] {validation['reason']}")
            return

        # Distancia de mercado
        market = self.exchange.get_market_price(parsed["symbol"])
        dist = self.validator.check_market_distance(parsed["entry"], market["price"])
        
        # Cálculo de riesgo
        balance = self.exchange.get_balance()["balance"]
        risk_pct = parsed.get("risk_pct", 1.0)
        risk = self.risk_manager.calculate_position_size(balance, risk_pct, parsed["entry"], parsed["sl"])
        
        if "error" in risk: return

        # Ejecución
        order = self.exchange.create_order(
            parsed["symbol"], parsed["side"], "limit", risk["position_size"] / parsed["entry"], parsed["entry"]
        )
        
        if order["status"] == "success":
            logger.info(f"  [ÉXITO] Trade abierto: {order['order_id']}")
            sid = self.db.save_signal(raw_text, **parsed)["id"]
            self.db.save_trade(sid, parsed["symbol"], parsed["side"], parsed["entry"])
            self.exchange.set_sl_tp(parsed["symbol"], parsed["sl"], parsed["tp"])

    async def handle_management_order(self, category, data):
        """Lógica de gestión de trades activos (Parciales, BE, Cierres)."""
        symbol = data.get("symbol", "UNKNOWN")
        
        # Intentamos buscar el símbolo si no viene (ej: "cerramos todo" en un chat monográfico)
        if symbol == "UNKNOWN":
            active = self.db.get_active_trades()
            if len(active) == 1:
                symbol = active[0]["symbol"]
            else:
                logger.error("  [Error] No se pudo determinar el símbolo para la gestión.")
                return

        logger.info(f"  [Gestión] Ejecutando {category} para {symbol}")

        if category == "PARTIAL_CLOSE":
            percent = data.get("percent", 30) / 100.0
            logger.info(f"  [Gestión] Ejecutando PARTIAL_CLOSE ({percent*100}%) para {symbol}")
            self.exchange.close_position_partial(symbol, pct=percent)
            
            # REGLA DE ORO: Si tomamos parcial, movemos SL a BE
            logger.info(f"  [Regla] Protegiendo trade: Moviendo SL a Break-Even para {symbol}")
            pos = self.exchange.get_position(symbol)
            if pos and pos.get("entry_price", 0) > 0:
                self.exchange.update_sl(symbol, pos["entry_price"])

        elif category == "MOVE_BE":
                trade = self.db.get_trade_by_symbol(symbol)
                if trade:
                    self.exchange.update_sl(symbol, trade["entry_price"])
                    self.db.update_trade_status(trade["id"], tp1_hit=True, sl_moved=True)
                    logger.info("  [Auto] SL movido a Break-Even tras toma de beneficios.")

if __name__ == "__main__":
    # Test rápido de orquestación manual
    print("Iniciando Trading Engine (Modo Test)")
