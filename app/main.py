from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db, init_db
from app.models import Booking
from pydantic import BaseModel
from typing import List, Optional


class BookingCreate(BaseModel):
    client_name: str
    client_phone: str
    service_type: str
    booking_date: datetime


class BookingResponse(BaseModel):
    id: int
    client_name: str
    client_phone: str
    service_type: str
    booking_date: datetime
    status: str
    amount: float

    class Config:
        from_attributes = True


app = FastAPI(title="Lashes Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ App started with PostgreSQL")


@app.get("/")
async def root():
    return {"message": "Lashes Booking API", "database": "PostgreSQL"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/bookings", response_model=BookingResponse)
async def create_booking(booking: BookingCreate, db: AsyncSession = Depends(get_db)):
    if booking.booking_date <= datetime.now():
        raise HTTPException(400, "Date must be in future")

    db_booking = Booking(
        client_name=booking.client_name,
        client_phone=booking.client_phone,
        service_type=booking.service_type,
        booking_date=booking.booking_date,
        status="pending"
    )
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)
    return db_booking


@app.get("/api/bookings", response_model=List[BookingResponse])
async def get_bookings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking))
    return result.scalars().all()