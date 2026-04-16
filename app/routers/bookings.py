from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models import Booking, Client
from app.schemas import BookingCreate, BookingResponse, PaymentResponse
from app.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=BookingResponse)
async def create_booking(
        booking: BookingCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    # Проверка даты
    if booking.booking_date <= datetime.now():
        raise HTTPException(status_code=400, detail="Booking date must be in future")

    # Проверка существующей записи на это время (упрощённо)
    existing = await db.execute(
        select(Booking).where(
            Booking.booking_date == booking.booking_date,
            Booking.status.in_(['pending', 'paid', 'confirmed'])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Time slot already booked")

    # Создание записи
    db_booking = Booking(
        client_name=booking.client_name,
        client_phone=booking.client_phone,
        service_type=booking.service_type,
        booking_date=booking.booking_date,
        master_id=booking.master_id,
        status="pending"
    )
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)

    # Фоновая задача: отправить уведомление через 30 мин если не оплачено
    background_tasks.add_task(check_payment_reminder, db_booking.id)

    logger.info(f"Booking created: {db_booking.id} for {booking.client_phone}")
    return db_booking


@router.get("/", response_model=list[BookingResponse])
async def get_bookings(
        skip: int = 0,
        limit: int = 100,
        status: str = None,
        db: AsyncSession = Depends(get_db)
):
    query = select(Booking)
    if status:
        query = query.where(Booking.status == status)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    bookings = result.scalars().all()
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/{booking_id}/cancel")
async def cancel_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "paid":
        raise HTTPException(status_code=400, detail="Cannot cancel paid booking")

    booking.status = "cancelled"
    await db.commit()
    return {"message": "Booking cancelled successfully"}


async def check_payment_reminder(booking_id: int):
    # Заглушка для напоминания
    import asyncio
    await asyncio.sleep(30 * 60)  # 30 минут
    logger.info(f"Reminder: Booking {booking_id} still pending payment")