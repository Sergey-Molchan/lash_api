from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime
from app.database import get_db
from app.models import Booking, Price

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/month/{year}/{month}")
async def get_month_finance(year: int, month: int, db: AsyncSession = Depends(get_db)):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    result = await db.execute(
        select(Booking)
        .where(
            Booking.booking_date >= start_date,
            Booking.booking_date < end_date,
            Booking.status.in_(['confirmed', 'paid'])
        )
        .order_by(Booking.booking_date)
    )
    bookings = result.scalars().all()

    prices_result = await db.execute(select(Price))
    prices = {p.service: p.price for p in prices_result.scalars().all()}

    service_stats = {
        "lashes": {"name": "Наращивание ресниц", "count": 0, "total": 0},
        "brows": {"name": "Ламинирование бровей", "count": 0, "total": 0},
        "complex": {"name": "Комплекс (ресницы+брови)", "count": 0, "total": 0}
    }

    total_amount = 0
    for b in bookings:
        service = b.service_type
        if service in service_stats:
            price = prices.get(service, 0)
            service_stats[service]["count"] += 1
            service_stats[service]["total"] += price
            total_amount += price

    return {
        "year": year,
        "month": month,
        "total_bookings": len(bookings),
        "total_amount": total_amount,
        "service_stats": service_stats
    }


@router.get("/monthly")
async def get_monthly_stats(db: AsyncSession = Depends(get_db)):
    """Статистика по всем месяцам (для графика)"""
    result = await db.execute(
        select(
            extract('year', Booking.booking_date).label('year'),
            extract('month', Booking.booking_date).label('month'),
            func.count(Booking.id).label('count')
        )
        .where(Booking.status.in_(['confirmed', 'paid']))
        .group_by('year', 'month')
        .order_by(extract('year', Booking.booking_date), extract('month', Booking.booking_date))
    )

    monthly_counts = {}
    for row in result:
        year = int(row.year)
        month = int(row.month)
        key = f"{year}-{month:02d}"
        monthly_counts[key] = row.count

    # Получаем цены
    prices_result = await db.execute(select(Price))
    prices = {p.service: p.price for p in prices_result.scalars().all()}

    # Получаем все записи для расчёта выручки по месяцам
    all_bookings = await db.execute(
        select(Booking).where(Booking.status.in_(['confirmed', 'paid']))
    )

    monthly_revenue = {}
    for b in all_bookings.scalars().all():
        key = b.booking_date.strftime("%Y-%m")
        price = prices.get(b.service_type, 0)
        monthly_revenue[key] = monthly_revenue.get(key, 0) + price

    months = []
    revenues = []
    for key in sorted(monthly_revenue.keys()):
        months.append(key)
        revenues.append(monthly_revenue[key])

    return {
        "months": months,
        "revenues": revenues,
        "counts": [monthly_counts.get(m, 0) for m in months]
    }