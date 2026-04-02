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
        source TEXT DEFAULT 'Global',
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
        margin REAL DEFAULT 0,
        tp1_hit INTEGER DEFAULT 0,
        sl_moved INTEGER DEFAULT 0,
        exit_price REAL,
        status TEXT DEFAULT 'open',
        FOREIGN KEY (signal_id) REFERENCES signals (id)
    )
    """)
    
    # Migración: Añadir columna margin si no existe
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN margin REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass # La columna ya existe

    # Migración: Añadir columna source si no existe en signals
    try:
        cursor.execute("ALTER TABLE signals ADD COLUMN source TEXT DEFAULT 'Global'")
    except sqlite3.OperationalError:
        pass

    # Migración: Añadir columna source si no existe en events
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN source TEXT DEFAULT 'Global'")
    except sqlite3.OperationalError:
        pass

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
        metadata TEXT,
        source TEXT DEFAULT 'Global'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        name TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # Inserción de valores por defecto (Si no existen)
    default_settings = [
        ("risk_strategy", "CAP"),        # "CAP" o "DISCARD"
        ("max_leverage", "10"),
        ("max_total_margin_usdt", "300"),
        ("max_trade_margin_usdt", "100"),
        ("risk_per_trade_pct", "1.0"),
        ("monitored_chats", "RETO 1k a 10k")
    ]
    for name, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (name, value) VALUES (?, ?)", (name, val))
        
    conn.commit()

init_db()

@mcp.tool()
def save_signal(raw_text: str, symbol: str, side: str, entry: float, tp: float, sl: float, risk: float, source: str = "Global"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO signals (raw_text, symbol, side, entry, tp, sl, risk, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (raw_text, symbol, side, entry, tp, sl, risk, source)
    )
    signal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": signal_id}

@mcp.tool()
def log_event(event_type: str, message: str, metadata: dict = None, source: str = "Global"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (event_type, message, metadata, source) VALUES (?, ?, ?, ?)",
        (event_type, message, json.dumps(metadata) if metadata else None, source)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}

@mcp.tool()
def save_trade(signal_id: int, symbol: str, side: str, entry_price: float, margin: float = 0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO trades (signal_id, symbol, side, entry_price, margin) VALUES (?, ?, ?, ?, ?)",
        (signal_id, symbol, side, entry_price, margin)
    )
    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "trade_saved", "id": trade_id}

@mcp.tool()
def get_trades():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    res = cursor.fetchall()
    conn.close()
    return res

@mcp.tool()
def get_active_trades():
    """
    Returns a list of all trades that haven't been closed, joined with signal targets.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, s.tp, s.sl, s.source
        FROM trades t 
        JOIN signals s ON t.signal_id = s.id 
        WHERE t.status = 'open'
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
        updates.append("status = 'closed'")
    
    if updates:
        params.append(trade_id)
        cursor.execute(f"UPDATE trades SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {"status": "success", "updated": updates}

@mcp.tool()
def get_settings():
    """
    Returns all trading settings as a dictionary.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings")
    settings = {row["name"]: row["value"] for row in cursor.fetchall()}
    conn.close()
    return settings

@mcp.tool()
def update_setting(name: str, value: str):
    """
    Updates or inserts a trading setting.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)", (name, str(value)))
    conn.commit()
    conn.close()
    return {"status": "success", "setting": name, "new_value": value}

if __name__ == "__main__":
    init_db()
    mcp.run()
