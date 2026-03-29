from fastmcp import FastMCP
import sqlite3
import json

mcp = FastMCP("db")
DB_PATH = "trading.db"

# Database initialization
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
        tp1_hit INTEGER DEFAULT 0,
        sl_moved INTEGER DEFAULT 0,
        exit_price REAL,
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
def get_active_trades():
    """
    Returns a list of all trades that haven't been closed, joined with signal targets.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, s.tp, s.sl 
        FROM trades t 
        JOIN signals s ON t.signal_id = s.id 
        WHERE t.exit_price IS NULL
    """)
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return trades

@mcp.tool()
def update_trade_status(trade_id: int, tp1_hit: bool = None, sl_moved: bool = None, exit_price: float = None):
    """
    Updates the status or exit price of a trade.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updates = []
    params = []
    if tp1_hit is not None:
        updates.append("tp1_hit = ?")
        params.append(1 if tp1_hit else 0)
    if sl_moved is not None:
        updates.append("sl_moved = ?")
        params.append(1 if sl_moved else 0)
    if exit_price is not None:
        updates.append("exit_price = ?")
        params.append(exit_price)
    
    if updates:
        params.append(trade_id)
        cursor.execute(f"UPDATE trades SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {"status": "success", "updated": updates}

@mcp.tool()
def log_event(event_type: str, message: str, metadata: dict = None):
    cursor.execute(
        "INSERT INTO events (event_type, message, metadata) VALUES (?, ?, ?)",
        (event_type, message, json.dumps(metadata) if metadata else None)
    )
    conn.commit()
    return {"status": "event_logged"}

if __name__ == "__main__":
    init_db()
    mcp.run()
