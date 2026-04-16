import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = None

async def connect_redis():
    global redis_client
    redis_client = await redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    await redis_client.ping()
    print(f"✅ Redis connected on port {REDIS_PORT}")
    return redis_client

async def close_redis():
    if redis_client:
        await redis_client.close()