from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime
from app.database import get_db
from app.models import Booking, Price

router = APIRouter(prefix="/api/finance", tags=["finance"])


async def get_price_for_booking(booking: Booking, db: AsyncSession) -> int:
    """Получить цену для конкретной записи с учётом объёма ресниц"""
    result = await db.execute(select(Price).where(Price.service == booking.service_type))
    price_obj = result.scalar_one_or_none()

    # Если ресницы и есть объём — используем цену с объёмом
    if booking.service_type == 'lashes' and booking.lashes_volume:
        volume_key = f"lashes_{booking.lashes_volume}"
        result = await db.execute(select(Price).where(Price.service == volume_key))
        volume_price = result.scalar_one_or_none()
        if volume_price:
            return volume_price.price

    return price_obj.price if price_obj else 0


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

    # Получаем цены
    prices_result = await db.execute(select(Price))
    prices = {p.service: p.price for p in prices_result.scalars().all()}

    service_stats = {
        "lashes": {"name": "Наращивание ресниц", "count": 0, "total": 0},
        "brows": {"name": "Ламинирование бровей", "count": 0, "total": 0},
        "complex": {"name": "Комплекс (ресницы+брови)", "count": 0, "total": 0}
    }

    # Статистика по объёмам ресниц
    volume_stats = {
        "1d": {"name": "1D (классика)", "count": 0, "total": 0},
        "2d": {"name": "2D (полуобъём)", "count": 0, "total": 0},
        "3d": {"name": "3D (объём)", "count": 0, "total": 0}
    }

    total_amount = 0
    for b in bookings:
        # Определяем цену
        if b.service_type == 'lashes' and b.lashes_volume:
            volume_key = f"lashes_{b.lashes_volume}"
            price = prices.get(volume_key, 0)
            if b.lashes_volume in volume_stats:
                volume_stats[b.lashes_volume]["count"] += 1
                volume_stats[b.lashes_volume]["total"] += price
        else:
            price = prices.get(b.service_type, 0)

        if b.service_type in service_stats:
            service_stats[b.service_type]["count"] += 1
            service_stats[b.service_type]["total"] += price

        total_amount += price

    return {
        "year": year,
        "month": month,
        "total_bookings": len(bookings),
        "total_amount": total_amount,
        "service_stats": service_stats,
        "volume_stats": volume_stats
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

        if b.service_type == 'lashes' and b.lashes_volume:
            volume_key = f"lashes_{b.lashes_volume}"
            price = prices.get(volume_key, 0)
        else:
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