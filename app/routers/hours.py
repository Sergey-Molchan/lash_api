from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.database import get_db
from app.models import DayHours, Booking
import json

router = APIRouter(prefix="/api/hours", tags=["hours"])

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
        day_hours = DayHours(date=date_str, closed_hours=json.dumps(closed_hours), break_start=break_start, break_end=break_end)
        db.add(day_hours)
    await db.commit()
    return {"ok": True}

@router.get("/booked-slots/{date}")
async def get_booked_slots(date: str, db: AsyncSession = Depends(get_db)):
    target_date = datetime.fromisoformat(date).date()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    result = await db.execute(select(Booking).where(Booking.booking_date >= start, Booking.booking_date <= end, Booking.status.in_(['pending', 'confirmed'])))
    bookings = result.scalars().all()
    return {"slots": [b.booking_date.strftime("%H:%M") for b in bookings]}

@router.get("/", response_class=HTMLResponse)
async def hours_page():
    with open("app/templates/hours.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())