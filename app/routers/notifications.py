import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Booking

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Шаблоны сообщений
TEMPLATES = {
    "booking_created": "✅ {studio}: Ваша запись на {date} создана. Ожидайте подтверждения.",
    "booking_confirmed": "✅ {studio}: Ваша запись на {date} ПОДТВЕРЖДЕНА! Ждём вас.",
    "booking_cancelled": "❌ {studio}: Запись на {date} отменена. Средства вернутся в течение 7 дней.",
    "booking_reminder": "🔔 {studio}: Напоминание! Завтра в {time} ваша процедура. Адрес: {address}",
}


@router.post("/send/{booking_id}/{type}")
async def send_notification(
        booking_id: int,
        type: str,
        db: AsyncSession = Depends(get_db)
):
    """Отправить уведомление (временно отключено)"""
    if type not in TEMPLATES:
        raise HTTPException(400, "Неизвестный тип уведомления")

    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Бронирование не найдено")

    # Формируем текст сообщения
    date_str = booking.booking_date.strftime("%d.%m.%Y %H:%M")
    message = TEMPLATES[type].format(
        studio="Lash Studio",
        date=date_str,
        time=booking.booking_date.strftime("%H:%M"),
        address="ул. Голубые Дали, 78, Адлер"
    )

    # Временно: просто выводим в лог, вместо отправки в Redis
    print(f"📱 Уведомление для {booking.client_phone}: {message}")

    return {"ok": True, "message": "Уведомление (отладочный режим)"}