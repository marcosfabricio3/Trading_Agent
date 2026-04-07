import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import app
sys.path.append(os.getcwd())

load_dotenv()

from app.dashboard_api import get_status
from app.services import exchange

async def test():
    print("Executing get_status()...")
    try:
        res = await get_status()
        print("RESULT SUCCESS:", res)
    except Exception as e:
        print("RESULT ERROR:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
