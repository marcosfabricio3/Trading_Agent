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

    def process_signal(self, raw_text: str):
        """
        Procesa una señal de texto desde su recepción hasta su ejecución.
        """
        logger.info("[Engine] Procesando nueva señal...")
        
        # 1. Parsing: Extraer datos brutos
        parsed = self.parser.parse_signal(raw_text)
        if "error" in parsed:
            logger.error(f"  [Error] Fallo al parsear: {parsed['error']}")
            self.db.log_event("parser_error", parsed["error"], {"raw": raw_text})
            return
            
        logger.info(f"  [OK] Señal parseada: {parsed['symbol']} {parsed['side']}")

        # 2. Validation: Verificar reglas de negocio
        validation = self.validator.validate_signal(parsed)
        if not validation["valid"]:
            logger.warning(f"  [Rechazada] Reglas de negocio: {validation['reason']}")
            self.db.log_event("validation_rejected", validation["reason"], parsed)
            return

        logger.info(f"  [OK] Validación exitosa (R:R: {validation['rr_ratio']})")

        # 2.1 Anti-Overload: Un trade por símbolo
        current_pos = self.exchange.get_position(parsed["symbol"])
        if current_pos.get("size", 0) > 0:
            logger.warning(f"  [Rechazada] Posición ya abierta para {parsed['symbol']}")
            self.db.log_event("overload_prevention", "Duplicate symbol position", parsed)
            return

        # 2.2 Market Distance: Validar que el precio no se haya escapado
        market_price = self.exchange.get_market_price(parsed["symbol"])["price"]
        dist_check = self.validator.check_market_distance(parsed["entry"], market_price)
        if not dist_check["valid"]:
            logger.warning(f"  [Rechazada] Precio de mercado muy lejano: {dist_check['distance_pct']}%")
            self.db.log_event("market_distance_rejected", dist_check["reason"], parsed)
            return

        logger.info(f"  [OK] Precio de mercado validado (Distancia: {dist_check['distance_pct']}%)")

        # 3. Risk Management: Calcular tamaño de posición
        balance = self.exchange.get_balance()["balance"]
        risk_calc = self.risk_manager.calculate_position_size(
            capital=balance,
            risk_pct=parsed["risk_pct"],
            entry=parsed["entry"],
            sl=parsed["sl"]
        )
        
        if "error" in risk_calc:
            logger.error(f"  [Error] Fallo en cálculo de riesgo: {risk_calc['error']}")
            return

        logger.info(f"  [OK] Posición calculada: {risk_calc['position_size']} USDT")

        # 4. Execution: Mandar orden al exchange
        order = self.exchange.create_order(
            symbol=parsed["symbol"],
            side=parsed["side"],
            order_type="limit",
            qty=risk_calc["position_size"] / parsed["entry"], 
            price=parsed["entry"]
        )
        
        if order["status"] == "success":
            logger.info(f"  [ÉXITO] Orden creada: {order['order_id']}")
            # 5. DB: Guardar todo el proceso
            signal_id = self.db.save_signal(
                raw_text=raw_text,
                symbol=parsed["symbol"],
                side=parsed["side"],
                entry=parsed["entry"],
                tp=parsed["tp"],
                sl=parsed["sl"],
                risk=parsed["risk_pct"]
            )["id"]
            
            self.db.save_trade(
                signal_id=signal_id,
                symbol=parsed["symbol"],
                side=parsed["side"],
                entry_price=parsed["entry"]
            )
            
            self.exchange.set_sl_tp(parsed["symbol"], parsed["sl"], parsed["tp"])
        else:
            logger.error(f"  [Error] Fallo en la ejecución del exchange: {order}")

if __name__ == "__main__":
    # Test rápido de orquestación manual
    print("Iniciando Trading Engine (Modo Test)")
