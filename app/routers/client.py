from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Booking, WorkingHours, DayHours
from pydantic import BaseModel, field_validator
import re
import json

router = APIRouter(prefix="/api/client", tags=["client"])

SERVICE_DURATION = {
    "lashes": 2.5,
    "brows": 1.0,
    "complex": 3.0
}


class BookingCreate(BaseModel):
    client_name: str
    client_phone: str
    service_type: str
    lashes_volume: str = None
    booking_date: datetime
    comment: str = None

    @field_validator('client_phone')
    def validate_phone(cls, v):
        # Удаляем все не-цифры и плюс
        cleaned = re.sub(r'[^0-9+]', '', v)

        # Если пусто
        if not cleaned or len(cleaned) == 0:
            raise HTTPException(400, '❌ Пожалуйста, введите номер телефона')

        # Подсчет цифр
        digits_only = re.sub(r'[^0-9]', '', cleaned)

        # Проверка длины
        if len(digits_only) < 10:
            missing = 10 - len(digits_only)
            word = 'цифры' if missing == 1 else 'цифр'
            raise HTTPException(400, f'❌ В вашем номере не хватает {missing} {word}. Пример: +7 999 123 45 67')

        if len(digits_only) > 11:
            raise HTTPException(400, '❌ Номер телефона слишком длинный (максимум 11 цифр)')

        # Приводим к формату +7XXXXXXXXXX
        if cleaned.startswith('+7') and len(cleaned) == 12:
            return cleaned
        elif cleaned.startswith('8') and len(cleaned) == 11:
            return '+7' + cleaned[1:]
        elif cleaned.startswith('7') and len(cleaned) == 11:
            return '+7' + cleaned[1:]
        elif len(digits_only) == 10:
            return '+7' + digits_only
        elif len(digits_only) == 11:
            if digits_only.startswith('7'):
                return '+7' + digits_only[1:]
            elif digits_only.startswith('8'):
                return '+7' + digits_only[1:]
            else:
                return '+7' + digits_only
        else:
            raise HTTPException(400, '❌ Неверный формат номера телефона. Пример: +7 999 123 45 67')


@router.post("/book", response_model=dict)
async def create_booking(booking: BookingCreate, db: AsyncSession = Depends(get_db)):
    # Проверка даты в будущем
    if booking.booking_date <= datetime.now():
        raise HTTPException(400, "❌ Дата записи должна быть в будущем")

    duration = SERVICE_DURATION.get(booking.service_type, 1.0)
    booking_end = booking.booking_date + timedelta(hours=duration)

    # Проверяем пересечения с существующими записями
    existing_bookings = await db.execute(
        select(Booking).where(
            Booking.booking_date >= booking.booking_date - timedelta(hours=3),
            Booking.booking_date <= booking_end,
            Booking.status.in_(['pending', 'confirmed'])
        )
    )

    for existing in existing_bookings.scalars().all():
        existing_end = existing.booking_date + timedelta(hours=SERVICE_DURATION.get(existing.service_type, 1.0))
        if not (booking.booking_date >= existing_end or booking_end <= existing.booking_date):
            duration_hours = int(duration)
            duration_min = int((duration % 1) * 60)
            duration_text = f"{duration_hours} ч {duration_min} мин" if duration_min > 0 else f"{duration_hours} ч"

            raise HTTPException(
                400,
                f"❌ Время {booking.booking_date.strftime('%H:%M')} не подходит для {booking.service_type} (длительность {duration_text}). "
                f"Выберите время, когда будет свободно {duration_text} подряд."
            )

    db_booking = Booking(
        client_name=booking.client_name,
        client_phone=booking.client_phone,
        service_type=booking.service_type,
        lashes_volume=booking.lashes_volume if booking.service_type == 'lashes' else None,
        booking_date=booking.booking_date,
        status="pending",
        notes=booking.comment
    )
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)

    return {"id": db_booking.id, "status": "pending", "message": "✅ Запись создана! Ожидайте подтверждения."}