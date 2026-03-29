from fastmcp import FastMCP
import sqlite3
import json

mcp = FastMCP("db")

# Database initialization
conn = sqlite3.connect("trading.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        raw_text TEXT,
        symbol TEXT,
        side TEXT,
        entry REAL,
        tp REAL,
        sl REAL,
        risk REAL,
        status TEXT DEFAULT 'received'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_id INTEGER,
        symbol TEXT,
        side TEXT,
        entry_price REAL,
        status TEXT DEFAULT 'open',
        FOREIGN KEY (signal_id) REFERENCES signals (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER,
        external_id TEXT,
        symbol TEXT,
        side TEXT,
        type TEXT,
        price REAL,
        qty REAL,
        status TEXT,
        FOREIGN KEY (trade_id) REFERENCES trades (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE,
        side TEXT,
        avg_price REAL,
        qty REAL,
        leverage INTEGER,
        unrealized_pnl REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT,
        message TEXT,
        metadata TEXT
    )
    """)
    conn.commit()

init_db()

@mcp.tool()
def save_signal(raw_text: str, symbol: str, side: str, entry: float, tp: float, sl: float, risk: float):
    cursor.execute(
        "INSERT INTO signals (raw_text, symbol, side, entry, tp, sl, risk) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (raw_text, symbol, side, entry, tp, sl, risk)
    )
    conn.commit()
    return {"status": "signal_saved", "id": cursor.lastrowid}

@mcp.tool()
def save_trade(signal_id: int, symbol: str, side: str, entry_price: float):
    cursor.execute(
        "INSERT INTO trades (signal_id, symbol, side, entry_price) VALUES (?, ?, ?, ?)",
        (signal_id, symbol, side, entry_price)
    )
    conn.commit()
    return {"status": "trade_saved", "id": cursor.lastrowid}

@mcp.tool()
def get_trades():
    cursor.execute("SELECT * FROM trades")
    return cursor.fetchall()

@mcp.tool()
def log_event(event_type: str, message: str, metadata: dict = None):
    cursor.execute(
        "INSERT INTO events (event_type, message, metadata) VALUES (?, ?, ?)",
        (event_type, message, json.dumps(metadata) if metadata else None)
    )
    conn.commit()
    return {"status": "event_logged"}

if __name__ == "__main__":
    mcp.run()
