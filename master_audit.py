import sqlite3
import os

def master_audit():
    db_path = "trading.db"
    if not os.path.exists(db_path):
        print("ERROR: No existe trading.db")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener chats de la configuración actual
    cursor.execute("SELECT value FROM settings WHERE name = 'monitored_chats'")
    row = cursor.fetchone()
    if not row:
        print("ERROR: No hay chats configurados en settings.")
        return
        
    chats = [c.strip() for c in row[0].split(",") if c.strip()]
    
    print(f"Target chats: {chats}")
    
    # Insertamos en Global y en cada chat individual
    for chat in ["Global", *chats]:
        msg = f"AUDITORIA: El panel '{chat}' esta recibiendo datos correctamente. PRUEBA OK."
        cursor.execute(
            "INSERT INTO events (event_type, message, source) VALUES (?, ?, ?)",
            ("AI_THOUGHT", msg, chat)
        )
        print(f"OK: Message injected into '{chat}'")
        
    conn.commit()
    conn.close()
    print("--- MASTER AUDIT COMPLETED ---")

if __name__ == "__main__":
    master_audit()
