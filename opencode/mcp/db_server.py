from fastmcp import FastMCP
import sqlite3

mcp = FastMCP("db")

conn = sqlite3.connect("trading.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    side TEXT,
    entry REAL
)
""")
conn.commit()


@mcp.tool()
def save_trade(symbol: str, side: str, entry: float):
    cursor.execute(
        "INSERT INTO trades (symbol, side, entry) VALUES (?, ?, ?)",
        (symbol, side, entry)
    )
    conn.commit()
    return {"status": "saved"}


@mcp.tool()
def get_trades():
    cursor.execute("SELECT * FROM trades")
    return cursor.fetchall()


if __name__ == "__main__":
    mcp.run()