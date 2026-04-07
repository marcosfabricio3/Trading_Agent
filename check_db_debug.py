import sqlite3
import json

def check_db():
    conn = sqlite3.connect("trading.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== SETTINGS ===")
    try:
        cursor.execute("SELECT * FROM settings")
        for row in cursor.fetchall():
            print(f"{row['name']}: {row['value']}")
    except:
        print("Settings table not found or error.")
        
    print("\n=== LATEST EVENTS (Last 10) ===")
    try:
        cursor.execute("SELECT id, timestamp, event_type, message, source FROM events ORDER BY id DESC LIMIT 10")
        for row in cursor.fetchall():
            print(f"[{row['timestamp']}] {row['event_type']} | {row['source']} | {row['message'][:100]}")
    except:
        print("Events table not found or error.")
        
    conn.close()

if __name__ == "__main__":
    check_db()
