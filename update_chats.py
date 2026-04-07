import sqlite3

def update_monitored_chats():
    conn = sqlite3.connect("trading.db")
    cursor = conn.cursor()
    # Lista completa de chats solitados por el usuario
    chats = "Pribado bot, -5095821758, RETO 1k a 10k, HOT SIGNALS, -1003781128126, BITGET"
    cursor.execute("INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)", ("monitored_chats", chats))
    conn.commit()
    conn.close()
    print(f"Configuración actualizada con: {chats}")

if __name__ == "__main__":
    update_monitored_chats()
