import sqlite3
import os
import sys

def hard_reset():
    db_path = "trading.db"
    
    # 1. Borrar DB si existe
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"File {db_path} deleted successfully.")
        except Exception as e:
            print(f"Error removing DB: {e}")
            return

    # 2. Re-inicializar DB
    sys.path.append('.')
    try:
        from opencode.mcp.db_server import init_db
        init_db()
        print("Database structure re-created.")
    except Exception as e:
        print(f"Error initializing structure: {e}")
        return

    # 3. Configurar chats limpios
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Al resetear, comenzamos solo con Mensajes Guardados para que el usuario elija el resto
        settings = [
            ("risk_per_trade_pct", "1.0"),
            ("monitored_chats", "Mensajes Guardados (ME)")
        ]
        
        cursor.executemany("INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)", settings)
        
        # Limpieza adicional por seguridad si el archivo no se borró
        cursor.execute("DELETE FROM events")
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM signals")
        
        conn.commit()
        conn.close()
        print("Config inicializada con valores por defecto.")
        print("Historial de eventos, señales y trades vaciado.")
        print("--- HARD RESET COMPLETED ---")
    except Exception as e:
        print(f"Error injecting settings: {e}")

if __name__ == "__main__":
    hard_reset()
