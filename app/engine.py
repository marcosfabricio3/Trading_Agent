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

    async def process_signal(self, raw_text: str, source: str = "Global"):
        """
        Procesa un mensaje de Telegram (Señal o Gestión) usando el Pipeline de IA.
        """
        logger.info(f"[Engine] Analizando mensaje de {source}...")
        self.db.log_event("AI_THOUGHT", "Detectado mensaje entrante de Telegram... Iniciando pipeline de análisis.", {"service": "ENGINE"}, source=source)
        
        # 1. Interpretación (Categoría + Datos)
        interpretation = await self.parser.parse_signal(raw_text)
        category = interpretation.get("category", "DISCARD")
        data = interpretation.get("data", {})

        if category == "DISCARD" or category == "NOISE":
            logger.info(f"  [Ignorado] Motivo: {interpretation.get('reason', 'Ruido detectado')}")
            self.db.log_event("AI_THOUGHT", f"Mensaje ignorado: {interpretation.get('reason', 'No es una instrucción de trading')}", {"category": category}, source=source)
            return

        if category == "ERROR":
            logger.error(f"  [Error] Fallo en interpretación: {interpretation.get('reason')}")
            self.db.log_event("AI_THOUGHT", "Error crítico en interpretación de señal.", {"error": interpretation.get('reason')}, source=source)
            return

        # 2. Ejecución según Categoría equilibrada
        if category == "NEW_SIGNAL":
            # Verificación de seguridad mínima
            if not data or "symbol" not in data:
                logger.warning(f"  [Rechazada] Datos insuficientes para NEW_SIGNAL: {data}")
                self.db.log_event("AI_THOUGHT", "Señal rechazada: Faltan datos críticos (Symbol/Side).", source=source)
                return
            await self.handle_new_signal(data, raw_text, source=source)
            
        elif category in ["PARTIAL_CLOSE", "MOVE_BE", "CLOSE_FULL"]:
            if not data or "symbol" not in data:
                 # Intentamos recuperación de símbolo desde la DB si es gestión
                 active = self.db.get_active_trades()
                 if len(active) == 1:
                     data["symbol"] = active[0]["symbol"]
                 else:
                    logger.warning(f"  [Error] No se puede gestionar sin símbolo claro.")
                    self.db.log_event("AI_THOUGHT", "Gestión fallida: No se detectó símbolo y hay múltiples trades.", source=source)
                    return
            await self.handle_management_order(category, data, source=source)
            
        else:
            logger.warning(f"  [Alerta] Categoría no procesable en este flujo: {category}")

    async def handle_new_signal(self, parsed, raw_text, source="Global"):
        """Lógica original de apertura de trades."""
        symbol = parsed['symbol']
        side = parsed['side'].lower()
        logger.info(f"  [OK] Nueva señal detectada: {symbol} {side}")
        self.db.log_event("AI_THOUGHT", f"Señal detectada para {symbol} ({side.upper()}). Iniciando validación...", {"symbol": symbol}, source=source)
        
        # Normalización de Side
        if side not in ["long", "short"]:
            logger.warning(f"  [Rechazada] Invalid side: {side}")
            self.db.log_event("AI_THOUGHT", f"Operación rechazada: Lado '{side}' no válido.")
            return

        # Validación
        validation = self.validator.validate_signal(parsed)
        if not validation["valid"]:
            logger.warning(f"  [Rechazada] {validation['reason']}")
            self.db.log_event("AI_THOUGHT", f"Validación fallida: {validation['reason']}", source=source)
            return
        
        self.db.log_event("AI_THOUGHT", "Validación exitosa. Calculando parámetros de riesgo y mercado...", source=source)

        # Distancia de mercado
        market = await self.exchange.get_market_price(parsed["symbol"])
        dist = self.validator.check_market_distance(parsed["entry"], market["price"])
        
        # 2. Análisis de Riesgo Dinámico
        balance_data = await self.exchange.get_balance()
        capital = balance_data.get("balance", 1000.0)
        
        # Obtenemos reglas de la DB
        settings = self.db.get_settings()
        risk_strat = settings.get("risk_strategy", "CAP")
        max_lev = int(settings.get("max_leverage", 10))
        max_total_margin = float(settings.get("max_total_margin_usdt", 300))
        max_trade_margin = float(settings.get("max_trade_margin_usdt", 100))
        default_risk = float(settings.get("risk_per_trade_pct", 1.0))
        
        # Calculamos margen actual
        active_trades = self.db.get_active_trades()
        current_margin = sum(float(t.get("margin", 0)) for t in active_trades)
        # Mejor: si tenemos el dato del trade lo usamos
        
        logger.info(f"  [Riesgo] Margen Actual: {current_margin:.2f} / Límite: {max_total_margin:.2f}")
        
        if current_margin >= max_total_margin:
            logger.warning(f"  [Rechazada] Límite de margen excedido ({current_margin:.2f} >= {max_total_margin:.2f})")
            self.db.log_event("ENGINE", f"Señal rechazada: Margen total {max_total_margin} agotado.", source=source)
            return

        risk_res = self.risk_manager.calculate_position_size(
            capital=capital,
            risk_pct=parsed.get("risk", default_risk),
            entry=parsed["entry"],
            sl=parsed["sl"],
            risk_strategy=risk_strat,
            max_trade_margin=max_trade_margin,
            max_total_margin=max_total_margin,
            current_total_margin=current_margin
        )
        
        if risk_res.get("status") == "DISCARDED":
            logger.warning(f"  [Rechazada] Regla de riesgo: {risk_res['reason']}")
            self.db.log_event("ENGINE", f"Señal rechazada: {risk_res['reason']}", source=source)
            return
            
        pos_size = risk_res["position_size"]

        # 3. Ejecución
        # Forzamos el apalancamiento máximo si el sugerido es mayor
        leverage = min(parsed.get("leverage", max_lev), max_lev)
        
        logger.info(f"  [Motor] Abriendo {parsed['symbol']} con {pos_size} USDT a {leverage}x")
        
        # Ejecución
        self.db.log_event("AI_THOUGHT", f"Enviando orden LIMIT a Bitget para {symbol} @ {parsed['entry']}...", source=source)
        order = await self.exchange.create_order(
            parsed["symbol"], parsed["side"], "limit", pos_size / parsed["entry"], parsed["entry"]
        )
        
        if order["status"] == "success":
            logger.info(f"  [ÉXITO] Trade abierto: {order['order_id']}")
            self.db.log_event("AI_THOUGHT", f"¡Operación abierta con éxito! ID: {order['order_id']}", {"order": order}, source=source)
            sid = self.db.save_signal(raw_text, source=source, **parsed)["id"]
            self.db.save_trade(sid, parsed["symbol"], parsed["side"], parsed["entry"], margin=pos_size)
            await self.exchange.set_sl_tp(parsed["symbol"], parsed["sl"], parsed["tp"])
        else:
            self.db.log_event("AI_THOUGHT", "Fallo en ejecución de orden en Exchange.", source=source)

    async def handle_management_order(self, category, data, source="Global"):
        """Lógica de gestión de trades activos (Parciales, BE, Cierres)."""
        symbol = data.get("symbol")
        
        # 1. Recuperación de Símbolo (Si es necesario)
        if not symbol or symbol == "UNKNOWN" or symbol == "ALL":
            active = self.db.get_active_trades()
            if not active:
                logger.info("  [Gestión] No hay operaciones activas para gestionar.")
                return
            
            # Si le pedimos gestionar UNA pero no dijo cuál y hay varias -> Error
            # Pero si es CLOSE_FULL sin moneda -> Procedemos con TODAS
            if category != "CLOSE_FULL" and len(active) > 1:
                logger.error(f"  [Error] Múltiples posiciones abiertas. Especifique moneda para {category}.")
                return
            
            if category == "CLOSE_FULL" and (not symbol or symbol == "ALL"):
                # CASO ESPECIAL: Liquidación Masiva
                logger.info(f"  [Gestión] Iniciando liquidación MASIVA de {len(active)} activos.")
                for t in active:
                    await self._execute_close(t["symbol"])
                return
            
            # Fallback al único símbolo activo
            symbol = active[0]["symbol"]

        logger.info(f"  [Gestión] Ejecutando {category} para {symbol}")

        if category == "PARTIAL_CLOSE":
            percent = data.get("percent", 30) / 100.0
            await self.exchange.close_position_partial(symbol, pct=percent)
            pos = await self.exchange.get_position(symbol)
            if pos and pos.get("entry_price", 0) > 0:
                await self.exchange.update_sl(symbol, pos["entry_price"])

        elif category == "CLOSE_FULL":
            await self._execute_close(symbol)

        elif category == "MOVE_BE":
            trade = self.db.get_trade_by_symbol(symbol)
            if trade:
                await self.exchange.update_sl(symbol, trade["entry_price"])
                self.db.update_trade_status(trade["id"], tp1_hit=True, sl_moved=True)
                logger.info(f"  [Auto] SL movido a Break-Even para {symbol} (Fuente: {source})")
                self.db.log_event("AI_THOUGHT", f"SL movido a Break-Even para {symbol}.", source=source)

    async def close_trade_by_id(self, trade_id: int):
        """Cierre de emergencia manual desde el Dashboard."""
        active = self.db.get_active_trades()
        target = next((t for t in active if t["id"] == trade_id), None)
        
        if not target:
            logger.warning(f"  [Error API] No se encontró trade activo con ID {trade_id}")
            return {"status": "error", "message": f"Trade {trade_id} no encontrado."}
            
        symbol = target["symbol"]
        source = target.get("source", "Global")
        
        logger.info(f"  [Gestión][Dashboard] Cierre de EMERGENCIA solicitado para {symbol} (ID: {trade_id})")
        self.db.log_event("ENGINE", f"Cierre manual solicitado desde Dashboard para {symbol}.", source=source)
        
        await self._execute_close(symbol)
        
        return {"status": "success", "symbol": symbol}

    async def _execute_close(self, symbol):
        """Helper para liquidar y limpiar DB."""
        logger.info(f"  [Gestión] Liquidando posición de {symbol}...")
        self.db.log_event("AI_THOUGHT", f"Cerrando {symbol} en Exchange y DB.")
        
        # 1. Exchange
        await self.exchange.close_position_full(symbol)
        
        # 2. DB (Buscamos los trades activos de ese símbolo)
        active_trades = self.db.get_active_trades()
        target_trades = [t for t in active_trades if t["symbol"] == symbol]
        
        for t in target_trades:
            # Obtenemos el precio actual como salida aproximada
            mkt = await self.exchange.get_market_price(symbol)
            self.db.update_trade_status(t["id"], exit_price=mkt["price"])
        
        logger.info(f"  [OK] Cierre completado para {symbol}.")

if __name__ == "__main__":
    # Test rápido de orquestación manual
    print("Iniciando Trading Engine (Modo Test)")
