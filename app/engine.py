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
        Retorna el 'Pensamiento' de la IA para feedback en Telegram.
        """
        logger.info(f"[Engine] Analizando mensaje de {source}...")
        self.db.log_event("AI_THOUGHT", "Detectado mensaje entrante de Telegram... Iniciando pipeline de análisis.", {"service": "ENGINE"}, source=source)
        
        # 1. Interpretación (Categoría + Datos)
        interpretation = await self.parser.parse_signal(raw_text)
        category = interpretation.get("category", "DISCARD")
        data = interpretation.get("data", {})
        thought = ""

        if category == "DISCARD" or category == "NOISE":
            reason = interpretation.get('reason', 'Ruido detectado')
            thought = f"🤔 No procesado: {reason}"
            logger.info(f"  [Ignorado] Motivo: {reason}")
            self.db.log_event("AI_THOUGHT", f"Mensaje ignorado: {reason}", {"category": category}, source=source)
            return thought

        if category == "ERROR":
            reason = interpretation.get('reason', 'Fallo desconocido')
            thought = f"❌ Error en análisis: {reason}"
            logger.error(f"  [Error] Fallo en interpretación: {reason}")
            self.db.log_event("AI_THOUGHT", "Error crítico en interpretación de señal.", {"error": reason}, source=source)
            return thought

        # 2. Ejecución según Categoría equilibrada
        if category == "NEW_SIGNAL":
            if not data or "symbol" not in data:
                thought = "⚠️ Datos insuficientes para abrir operación."
                logger.warning(f"  [Rechazada] {thought}")
                self.db.log_event("AI_THOUGHT", thought, source=source)
                return thought
            
            # Ejecutamos y atrapamos el resultado
            res = await self.handle_new_signal(data, raw_text, source=source)
            return res
            
        elif category in ["PARTIAL_CLOSE", "MOVE_BE", "CLOSE_FULL"]:
            if not data or "symbol" not in data:
                 active = self.db.get_active_trades()
                 if len(active) == 1:
                     data["symbol"] = active[0]["symbol"]
                 else:
                    thought = "⚠️ Gestión fallida: Múltiples trades abiertos, especifique moneda."
                    logger.warning(f"  [Error] {thought}")
                    self.db.log_event("AI_THOUGHT", thought, source=source)
                    return thought
            
            res = await self.handle_management_order(category, data, source=source)
            return res
            
        else:
            thought = f"🛸 Categoría '{category}' no procesable automáticamente."
            logger.warning(f"  [Alerta] {thought}")
            return thought

    async def handle_new_signal(self, parsed, raw_text, source="Global"):
        """Lógica original de apertura de trades. Retorna 'thought'."""
        symbol = parsed.get('symbol')
        side = parsed.get('side', '').lower()
        
        logger.info(f"  [OK] Nueva señal detectada: {symbol} {side}")
        self.db.log_event("AI_THOUGHT", f"Señal detectada para {symbol} ({side.upper()}). Iniciando normalización...", {"symbol": symbol}, source=source)
        
        # 1. Normalización de Side
        if side not in ["long", "short"]:
            thought = f"⚠️ Lado '{side}' no válido."
            self.db.log_event("AI_THOUGHT", f"Operación rechazada: {thought}")
            return thought

        # 2. Pre-procesamiento de Precios (Casting y Mercado)
        try:
            entry = parsed.get("entry", 0)
            order_type = "limit"
            # Manejo de "mercado" o 0
            if str(entry).lower() in ["mercado", "market", "0", "0.0"] or entry == 0:
                market_data = await self.exchange.get_market_price(symbol)
                if "price" in market_data:
                    entry = float(market_data["price"])
                    parsed["entry"] = entry
                    order_type = "market"
                    logger.info(f"  [Engine] Precio de entrada fijado a MERCADO: {entry}")
                else:
                    error_msg = market_data.get("error", "No se pudo obtener el precio de mercado")
                    logger.error(f"  [Error] No se pudo obtener el precio de mercado: {error_msg}")
                    self.db.log_event("ENGINE", f"❌ Error al obtener precio mercado: {error_msg}", source=source)
                    return f"❌ Error al obtener precio de mercado: {error_msg}"
            else:
                entry = float(entry)
                parsed["entry"] = entry

            # SL por defecto (2%) si no existe
            sl = parsed.get("sl", 0)
            if not sl or str(sl).lower() in ["0", "0.0"] or sl == 0:
                if side == "long":
                    sl = entry * 0.98 # 2% abajo
                else:
                    sl = entry * 1.02 # 2% arriba
                parsed["sl"] = float(sl)
                logger.info(f"  [Engine] SL no detectado. Aplicando SL automático (2%): {parsed['sl']}")

            # TP opcional (solo casting)
            tp = parsed.get("tp", 0)
            if tp:
                parsed["tp"] = float(tp)
            else:
                parsed["tp"] = 0.0

        except Exception as e:
            thought = f"⚠️ Error procesando precios: {str(e)}"
            logger.error(f"  [Error] {thought}")
            return thought

        # 3. Validación
        validation = self.validator.validate_signal(parsed)
        if not validation["valid"]:
            thought = f"⚠️ {validation['reason']}"
            logger.warning(f"  [Rechazada] {thought}")
            self.db.log_event("AI_THOUGHT", f"Validación fallida: {thought}", source=source)
            return thought
        
        self.db.log_event("AI_THOUGHT", "Validación exitosa. Calculando parámetros de riesgo...", source=source)

        # 4. Riesgo
        balance_data = await self.exchange.get_balance()
        capital = balance_data.get("balance", 1000.0)
        settings = self.db.get_settings()
        
        risk_res = self.risk_manager.calculate_position_size(
            capital=capital,
            risk_pct=float(parsed.get("risk", settings.get("risk_per_trade_pct", 1.0))),
            entry=float(parsed["entry"]),
            sl=float(parsed["sl"]),
            risk_strategy=settings.get("risk_strategy", "CAP"),
            max_trade_margin=float(settings.get("max_trade_margin_usdt", 100)),
            max_total_margin=float(settings.get("max_total_margin_usdt", 300)),
            current_total_margin=sum(float(t.get("margin", 0)) for t in self.db.get_active_trades()),
            min_notional_usdt=5.0 # Mínimo de seguridad para evitar errores de exchange
        )
        
        if risk_res.get("status") == "DISCARDED":
            thought = f"⚠️ Operación descartada: {risk_res['reason']}"
            logger.warning(f"  [Descartada] {thought}")
            self.db.log_event("ENGINE", thought, source=source)
            return thought
            
        pos_size = risk_res["position_size"]
        leverage = min(parsed.get("leverage", int(settings.get("max_leverage", 10))), int(settings.get("max_leverage", 10)))
        
        # 4.1 Establecer Apalancamiento antes de la orden
        try:
            await self.exchange.set_leverage(symbol, leverage)
            logger.info(f"  [Engine] Apalancamiento establecido a {leverage}x para {symbol}")
        except Exception as lev_err:
            logger.warning(f"  [Engine] No se pudo establecer apalancamiento: {lev_err}")

        # 4.2 Ajustar cantidad según lot_size del exchange
        market_info = await self.exchange.get_market_info(symbol)
        lot_size = market_info.get("lot_size", 0.001)
        precision = market_info.get("precision", {}).get("amount", 3)
        
        raw_qty = pos_size / parsed["entry"]
        # Aseguramos que sea al menos el mínimo lot_size
        qty = max(raw_qty, lot_size)
        
        # Redondear a la precisión del exchange
        import math
        qty = math.floor(qty * (10**precision)) / (10**precision)
        
        actual_margin = qty * parsed["entry"] / leverage
        logger.info(f"  [Engine] Cantidad final: {qty} (Basada en lot_size {lot_size}). Margen estimado: {actual_margin:.2f} USDT")

        # Ejecución
        order = await self.exchange.create_order(
            parsed["symbol"], parsed["side"], order_type, qty, parsed["entry"]
        )
        
        if order["status"] == "success":
            await self.exchange.set_sl_tp(parsed["symbol"], parsed["sl"], parsed["tp"])
            sid = self.db.save_signal(raw_text, source=source, **parsed)["id"]
            # Guardamos el margen REAL utilizado (estimado)
            self.db.save_trade(sid, parsed["symbol"], parsed["side"], parsed["entry"], margin=actual_margin)
            thought = f"✅ Trade abierto: {symbol} {side.upper()} @ {parsed['entry']} (Size: {actual_margin:.2f} USDT, Lev: {leverage}x)"
            self.db.log_event("AI_THOUGHT", f"¡Éxito! {thought}", source=source)
            return thought
        else:
            error_msg = order.get("message", "Error desconocido")
            thought = f"❌ Error al enviar orden al Exchange: {error_msg}"
            logger.error(f"  [Exchange] {thought}")
            self.db.log_event("AI_THOUGHT", thought, source=source)
            return thought

    async def handle_management_order(self, category, data, source="Global"):
        """Lógica de gestión de trades activos. Retorna 'thought'."""
        symbol = data.get("symbol")
        
        # 1. Recuperación de Símbolo
        if not symbol or symbol == "UNKNOWN" or symbol == "ALL":
            active = self.db.get_active_trades()
            if not active:
                return "ℹ️ No hay operaciones activas para gestionar."
            if category != "CLOSE_FULL" and len(active) > 1:
                return f"⚠️ Especifique moneda para {category} (Múltiples trades)."
            if category == "CLOSE_FULL" and (not symbol or symbol == "ALL"):
                for t in active: await self._execute_close(t["symbol"])
                return f"✅ Liquidación masiva completada ({len(active)} trades)."
            symbol = active[0]["symbol"]

        if category == "PARTIAL_CLOSE":
            pct = data.get("percent", 30)
            await self.exchange.close_position_partial(symbol, pct=pct/100.0)
            return f"✅ Cierre parcial del {pct}% ejecutado para {symbol}. SL movido a entrada."

        elif category == "CLOSE_FULL":
            await self._execute_close(symbol)
            return f"✅ Posición de {symbol} cerrada completamente."

        elif category == "MOVE_BE":
            trade = self.db.get_trade_by_symbol(symbol)
            if trade:
                await self.exchange.update_sl(symbol, trade["entry_price"])
                self.db.update_trade_status(trade["id"], tp1_hit=True, sl_moved=True)
                return f"🛡️ SL movido a Break-Even para {symbol}."
            return f"⚠️ No se encontró trade activo para {symbol}."
        
        return "ℹ️ Instrucción de gestión procesada."

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
