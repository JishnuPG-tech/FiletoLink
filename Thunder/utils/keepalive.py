# Thunder/utils/keepalive.py

import asyncio
import aiohttp
from Thunder.vars import Var
from Thunder.utils.logger import logger

async def ping_server():
    try:
        ping_url = f"http://127.0.0.1:{Var.PORT}/status"
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            while True:
                try:
                    await asyncio.sleep(Var.PING_INTERVAL)
                    async with session.get(ping_url, allow_redirects=False) as resp:
                        if resp.status not in (200, 302):
                            logger.warning(f"Ping to {ping_url} returned status {resp.status}.")
                except asyncio.CancelledError:
                    break
                except Exception as inner_e:
                    logger.warning(f"Keepalive ping note: {inner_e}")
    except Exception as e:
        logger.error(f"Error in ping_server: {e}", exc_info=True)
