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
    
    def clean_phone(self, phone: str) -> str:
        """Очищает и приводит номер к формату 7XXXXXXXXXX"""
        # Удаляем все символы кроме цифр
        cleaned = ''.join(filter(str.isdigit, phone))
        
        # Если номер начинается с 8, заменяем на 7
        if cleaned.startswith('8'):
            cleaned = '7' + cleaned[1:]
        
        # Если номер начинается с 7 и длина 11 цифр
        if cleaned.startswith('7') and len(cleaned) == 11:
            return cleaned
        
        # Если номер из 10 цифр (без кода страны), добавляем 7
        if len(cleaned) == 10:
            return '7' + cleaned
        
        return cleaned
    
    async def send_sms(self, phone: str, text: str) -> bool:
        if not SMSRU_API_KEY:
            print("❌ SMS.RU API ключ не настроен (добавьте SMSRU_API_KEY в .env)")
            return False
        
        # Приводим номер к правильному формату
        phone = self.clean_phone(phone)
        
        print(f"📱 Отправка SMS на номер: {phone}")
        
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
                    print(f"📨 Ответ SMS.RU: {data}")
                    
                    # Проверяем статус ответа
                    if data.get("status") == "OK":
                        # Проверяем статус отправки для каждого номера
                        if "sms" in data and data["sms"].get(phone, {}).get("status") == "OK":
                            print(f"✅ SMS отправлено на {phone}: {text[:50]}...")
                            return True
                        else:
                            error_code = data["sms"].get(phone, {}).get("status_code")
                            print(f"❌ Ошибка отправки на {phone}: код {error_code}")
                            return False
                    else:
                        print(f"❌ Ошибка API: {data}")
                        return False
            except Exception as e:
                print(f"❌ Ошибка отправки SMS: {e}")
                return False
    
    async def process_message(self, message):
        try:
            data = json.loads(message)
            phone = data.get("phone")
            text = data.get("text")
            booking_id = data.get("booking_id")
            
            if not phone or not text:
                print("❌ Неверный формат сообщения")
                return
            
            success = await self.send_sms(phone, text)
            print(f"{'✅' if success else '❌'} Уведомление для брони #{booking_id}")
            
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
    
    async def run(self):
        print("🚀 SMS Worker запущен, ожидание сообщений...")
        while self.running:
            try:
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
