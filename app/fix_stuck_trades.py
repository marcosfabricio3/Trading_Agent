import sqlite3
import os

# Buscamos la base de datos en la raíz
db_path = "trading_agent.db"

if not os.path.exists(db_path):
    print(f"Error: No se encontró {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Ver qué tenemos ahora
        cursor.execute("SELECT id, symbol, status FROM trades")
        rows = cursor.fetchall()
        print(f"--- Trades actuales ({len(rows)}) ---")
        for r in rows:
            print(f"ID: {r[0]} | Symbol: {r[1]} | Status: {r[2]}")
        
        # 2. Forzar el cierre de todo lo que esté en 'active'
        print("\nLimpiando trades activos...")
        cursor.execute("UPDATE trades SET status = 'closed' WHERE status = 'active'")
        conn.commit()
        
        print("Éxito: Se han cerrado todos los trades para detener el bucle.")
        conn.close()
    except Exception as e:
        print(f"Error de base de datos: {e}")
