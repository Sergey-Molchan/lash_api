import asyncio
import redis.asyncio as redis


async def main():
    # Подключаемся к Redis (порт 6380, потому что ваш контейнер на этом порту)
    r = await redis.from_url("redis://localhost:6380")

    # Пишем ключ 'hello' со значением 'world'
    await r.set("hello", "world")

    # Читаем ключ
    value = await r.get("hello")
    print(f"Значение из Redis: {value.decode()}")  # должно вывести 'world'

    await r.close()


asyncio.run(main())