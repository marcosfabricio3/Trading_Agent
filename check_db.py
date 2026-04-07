import sqlite3
import os

db_path = "trading.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, value FROM settings WHERE name = 'monitored_chats'")
    row = cursor.fetchone()
    if row:
        print(f"Chats en DB: {row[1]}")
    else:
        print("No hay chats monitoreados en la base de datos.")
    conn.close()
else:
    print("Base de datos no encontrada.")
