from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.database import get_db
from app.models import DayHours, Booking
import json

router = APIRouter(prefix="/api/hours", tags=["hours"])

# Длительность услуг
SERVICE_DURATION = {
    "lashes": 2.5,
    "brows": 1.0,
    "complex": 3.0
}


@router.get("/get/{date}")
async def get_day_hours(date: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DayHours).where(DayHours.date == date))
    day_hours = result.scalar_one_or_none()
    return {
        "closed_hours": json.loads(day_hours.closed_hours) if day_hours and day_hours.closed_hours else [],
        "break_start": day_hours.break_start if day_hours else None,
        "break_end": day_hours.break_end if day_hours else None
    }


@router.post("/save")
async def save_day_hours(data: dict, db: AsyncSession = Depends(get_db)):
    date_str = data.get("date")
    closed_hours = data.get("closed_hours", [])
    break_start = data.get("break_start")
    break_end = data.get("break_end")
    result = await db.execute(select(DayHours).where(DayHours.date == date_str))
    day_hours = result.scalar_one_or_none()
    if day_hours:
        day_hours.closed_hours = json.dumps(closed_hours)
        day_hours.break_start = break_start
        day_hours.break_end = break_end
    else:
        day_hours = DayHours(date=date_str, closed_hours=json.dumps(closed_hours), break_start=break_start,
                             break_end=break_end)
        db.add(day_hours)
    await db.commit()
    return {"ok": True}


@router.get("/booked-slots/{date}")
async def get_booked_slots(date: str, db: AsyncSession = Depends(get_db)):
    target_date = datetime.fromisoformat(date).date()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    result = await db.execute(
        select(Booking).where(
            Booking.booking_date >= start,
            Booking.booking_date <= end,
            Booking.status.in_(['pending', 'confirmed'])
        )
    )
    bookings = result.scalars().all()

    booked_slots = []
    for b in bookings:
        duration = SERVICE_DURATION.get(b.service_type, 1.0)
        end_time = b.booking_date + timedelta(hours=duration)
        slot_hours = []
        current = b.booking_date
        while current < end_time:
            slot_hours.append(current.strftime("%H:%M"))
            current += timedelta(hours=1)
        booked_slots.append({
            "id": b.id,
            "client_name": b.client_name,
            "client_phone": b.client_phone,
            "service_type": b.service_type,
            "start_time": b.booking_date.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "duration": duration,
            "occupied_hours": slot_hours,
            "comment": b.notes
        })
    return {"slots": booked_slots}


@router.post("/copy-to-week")
async def copy_hours_to_week(data: dict, db: AsyncSession = Depends(get_db)):
    source_date = data.get("source_date")
    hours_data = data.get("hours_data")
    source = datetime.fromisoformat(source_date)
    closed_hours = json.dumps(hours_data.get("closed_hours", []))
    break_start = hours_data.get("break_start")
    break_end = hours_data.get("break_end")
    for i in range(1, 8):
        next_date = (source + timedelta(days=i)).strftime("%Y-%m-%d")
        result = await db.execute(select(DayHours).where(DayHours.date == next_date))
        day_hours = result.scalar_one_or_none()
        if day_hours:
            day_hours.closed_hours = closed_hours
            day_hours.break_start = break_start
            day_hours.break_end = break_end
        else:
            day_hours = DayHours(date=next_date, closed_hours=closed_hours, break_start=break_start,
                                 break_end=break_end)
            db.add(day_hours)
    await db.commit()
    return {"ok": True}