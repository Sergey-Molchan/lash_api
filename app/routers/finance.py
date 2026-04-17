from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime
from app.database import get_db
from app.models import Booking

router = APIRouter(prefix="/api/finance", tags=["finance"])

@router.get("/month/{year}/{month}")
async def get_month_finance(year: int, month: int, db: AsyncSession = Depends(get_db)):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    bookings_result = await db.execute(
        select(Booking)
        .where(
            Booking.booking_date >= start_date,
            Booking.booking_date < end_date,
            Booking.status.in_(['confirmed', 'paid'])
        )
        .order_by(Booking.booking_date)
    )
    bookings = bookings_result.scalars().all()
    
    service_stats = {
        "lashes": {"name": "Наращивание ресниц", "count": 0, "total": 0},
        "brows": {"name": "Ламинирование бровей", "count": 0, "total": 0},
        "complex": {"name": "Комплекс (ресницы+брови)", "count": 0, "total": 0}
    }
    
    for b in bookings:
        service = b.service_type
        if service in service_stats:
            service_stats[service]["count"] += 1
            service_stats[service]["total"] += b.amount or 300
    
    return {
        "year": year,
        "month": month,
        "total_bookings": len(bookings),
        "total_amount": sum(b.amount or 300 for b in bookings),
        "service_stats": service_stats
    }
