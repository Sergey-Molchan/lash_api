from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from app.database import get_db
from app.models import Booking, Master
from app.schemas import BookingUpdate
from app.config import settings
import secrets

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/bookings")
async def admin_get_bookings(
        admin: str = Depends(verify_admin),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Booking).order_by(Booking.booking_date))
    bookings = result.scalars().all()
    return bookings


@router.put("/bookings/{booking_id}")
async def admin_update_booking(
        booking_id: int,
        booking_update: BookingUpdate,
        admin: str = Depends(verify_admin),
        db: AsyncSession = Depends(get_db)
):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking_update.booking_date:
        booking.booking_date = booking_update.booking_date
    if booking_update.status:
        booking.status = booking_update.status
    if booking_update.master_id is not None:
        booking.master_id = booking_update.master_id

    booking.updated_at = datetime.now()
    await db.commit()
    return {"message": "Booking updated successfully"}


@router.get("/masters")
async def get_masters(
        admin: str = Depends(verify_admin),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Master))
    masters = result.scalars().all()
    return masters


@router.post("/masters")
async def create_master(
        name: str,
        admin: str = Depends(verify_admin),
        db: AsyncSession = Depends(get_db)
):
    master = Master(name=name, is_active=True)
    db.add(master)
    await db.commit()
    return {"message": f"Master {name} created"}