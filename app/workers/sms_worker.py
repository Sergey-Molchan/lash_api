import asyncio
import os
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()

SMSRU_API_KEY = os.getenv("SMSRU_API_KEY")
SMSRU_SENDER = os.getenv("SMSRU_SENDER", "LashStudio")


class SMSWorker:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.queue_name = "sms_queue"
        self.running = True

    async def send_sms(self, phone: str, text: str) -> bool:
        """Отправка SMS через SMS.RU"""
        if not SMSRU_API_KEY:
            print("❌ SMS.RU API ключ не настроен (добавьте SMSRU_API_KEY в .env)")
            return False

        # Очищаем номер телефона
        phone = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

        url = "https://sms.ru/sms/send"
        params = {
            "api_id": SMSRU_API_KEY,
            "to": phone,
            "msg": text,
            "json": 1
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if data.get("status") == "OK":
                        print(f"✅ SMS отправлено на {phone}: {text[:50]}...")
                        return True
                    else:
                        print(f"❌ Ошибка SMS: {data}")
                        return False
            except Exception as e:
                print(f"❌ Ошибка отправки SMS: {e}")
                return False

    async def process_message(self, message):
        """Обработка одного сообщения из очереди"""
        try:
            data = json.loads(message)
            phone = data.get("phone")
            text = data.get("text")
            booking_id = data.get("booking_id")

            if not phone or not text:
                print("❌ Неверный формат сообщения")
                return

            success = await self.send_sms(phone, text)

            # Логируем результат
            print(f"{'✅' if success else '❌'} Уведомление для брони #{booking_id}: {text[:50]}...")

        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")

    async def run(self):
        """Основной цикл воркера"""
        print("🚀 SMS Worker запущен, ожидание сообщений...")
        while self.running:
            try:
                # Получаем сообщение из очереди (блокирующая операция)
                message = await self.redis.blpop(self.queue_name, timeout=5)
                if message:
                    await self.process_message(message[1])
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Ошибка воркера: {e}")
                await asyncio.sleep(1)

        print("🛑 SMS Worker остановлен")

    def stop(self):
        self.running = False