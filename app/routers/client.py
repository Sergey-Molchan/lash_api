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
        cleaned = re.sub(r'[^0-9+]', '', v)
        if cleaned.startswith('+7') and len(cleaned) == 12:
            return cleaned
        elif cleaned.startswith('8') and len(cleaned) == 11:
            return '+7' + cleaned[1:]
        elif cleaned.startswith('7') and len(cleaned) == 11:
            return '+7' + cleaned[1:]
        elif len(cleaned) == 10:
            return '+7' + cleaned
        elif len(cleaned) == 11 and not cleaned.startswith('+'):
            return '+7' + cleaned[1:]
        raise ValueError('Неверный формат номера телефона')


@router.post("/book", response_model=dict)
async def create_booking(booking: BookingCreate, db: AsyncSession = Depends(get_db)):
    if booking.booking_date <= datetime.now():
        raise HTTPException(400, "Дата должна быть в будущем")

    duration = SERVICE_DURATION.get(booking.service_type, 1.0)
    booking_end = booking.booking_date + timedelta(hours=duration)

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
            raise HTTPException(400, "Это время уже занято. Выберите другое время")

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

    return {"id": db_booking.id, "status": "pending", "message": "Запись создана"}


@router.get("/available-slots")
async def get_available_slots(date: str, db: AsyncSession = Depends(get_db)):
    target_date = datetime.fromisoformat(date).date()

    wh_result = await db.execute(
        select(WorkingHours).where(WorkingHours.date == target_date, WorkingHours.is_day_off == True))
    if wh_result.scalar_one_or_none():
        return {"slots": [], "is_day_off": True}

    dh_result = await db.execute(select(DayHours).where(DayHours.date == date))
    day_hours = dh_result.scalar_one_or_none()

    all_slots = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00']
    closed_hours = json.loads(day_hours.closed_hours) if day_hours and day_hours.closed_hours else []
    break_start = day_hours.break_start if day_hours else None
    break_end = day_hours.break_end if day_hours else None

    available = [slot for slot in all_slots if slot not in closed_hours]

    if break_start and break_end:
        break_hours = []
        current = datetime.strptime(break_start, "%H:%M")
        end = datetime.strptime(break_end, "%H:%M")
        while current < end:
            break_hours.append(current.strftime("%H:%M"))
            current += timedelta(hours=1)
        available = [slot for slot in available if slot not in break_hours]

    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    booked_result = await db.execute(
        select(Booking).where(
            Booking.booking_date >= start,
            Booking.booking_date <= end,
            Booking.status.in_(['pending', 'confirmed'])
        )
    )

    booked_slots = set()
    for b in booked_result.scalars().all():
        duration = SERVICE_DURATION.get(b.service_type, 1.0)
        slot_time = b.booking_date
        for i in range(int(duration) + (1 if duration % 1 > 0 else 0)):
            hour = (slot_time + timedelta(hours=i)).strftime("%H:%M")
            if hour >= "10:00" and hour <= "19:00":
                booked_slots.add(hour)

    final_slots = [slot for slot in available if slot not in booked_slots]
    return {"slots": final_slots, "is_day_off": False}