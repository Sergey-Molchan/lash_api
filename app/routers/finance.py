from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime
from app.database import get_db
from app.models import Booking

router = APIRouter(prefix="/api/finance", tags=["finance"])

@router.get("/stats")
async def get_finance_stats(db: AsyncSession = Depends(get_db)):
    """Получить статистику по месяцам"""
    
    monthly_stats = await db.execute(
        select(
            extract('year', Booking.booking_date).label('year'),
            extract('month', Booking.booking_date).label('month'),
            func.count(Booking.id).label('count'),
            func.sum(Booking.amount).label('total')
        )
        .where(Booking.status.in_(['confirmed', 'paid']))
        .group_by('year', 'month')
        .order_by(extract('year', Booking.booking_date).desc(), extract('month', Booking.booking_date).desc())
    )
    
    result = []
    for row in monthly_stats:
        result.append({
            "year": int(row.year),
            "month": int(row.month),
            "count": int(row.count),
            "total": float(row.total) if row.total else 0
        })
    
    return result

@router.get("/month/{year}/{month}")
async def get_month_finance(year: int, month: int, db: AsyncSession = Depends(get_db)):
    """Получить детальную статистику за конкретный месяц"""
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Получаем все подтверждённые записи за месяц
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
    
    # Статистика по услугам
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
        "month_name": get_month_name(month),
        "total_bookings": len(bookings),
        "total_amount": sum(b.amount or 300 for b in bookings),
        "service_stats": service_stats,
        "bookings": [
            {
                "id": b.id,
                "client_name": b.client_name,
                "client_phone": b.client_phone,
                "service_type": b.service_type,
                "booking_date": b.booking_date.isoformat(),
                "amount": b.amount or 300
            }
            for b in bookings
        ]
    }

def get_month_name(month: int) -> str:
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    return months[month - 1]
