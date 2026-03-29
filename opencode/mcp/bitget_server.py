from mcp import MCPServer

server = MCPServer("bitget")

@server.tool()
def create_order(symbol, side, price, qty):
    return {"status": "ok"}

@server.tool()
def get_balance():
    return {"balance": 1000}

server.run()