from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from datetime import datetime
from app.database import Base
import json

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    service_type = Column(String(50), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")
    amount = Column(Float, default=300.0)
    paid = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)  # комментарий к записи
    created_at = Column(DateTime, default=datetime.now)

class WorkingHours(Base):
    __tablename__ = "working_hours"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, unique=True)
    is_day_off = Column(Boolean, default=False)

class DayHours(Base):
    __tablename__ = "day_hours"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(20), nullable=False, unique=True)
    closed_hours = Column(Text, default="[]")
    break_start = Column(String(5), nullable=True)
    break_end = Column(String(5), nullable=True)

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(50), nullable=False, unique=True)
    price = Column(Integer, nullable=False, default=0)

class SiteContent(Base):
    __tablename__ = "site_content"
    id = Column(Integer, primary_key=True, index=True)
    section = Column(String(50), nullable=False, unique=True)
    content = Column(Text, nullable=False)

class GalleryImage(Base):
    __tablename__ = "gallery_images"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    rating = Column(Integer, default=5)
    text = Column(Text, nullable=False)
    emoji = Column(String(10), default="😊")
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, nullable=False, index=True)  # связь с бронированием
    payment_id = Column(String(100), unique=True, index=True)  # ID в платёжной системе
    amount = Column(Float, default=300.0)
    status = Column(String(20), default="pending")  # pending, paid, refunded, failed
    payment_method = Column(String(50), default="sbp")  # sbp, card
    payment_data = Column(Text, nullable=True)  # JSON с данными платежа
    paid_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class Refund(Base):
    __tablename__ = "refunds"
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, nullable=False, index=True)  # связь с платежом
    booking_id = Column(Integer, nullable=False, index=True)  # связь с бронированием
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, completed, failed
    refund_id = Column(String(100), nullable=True)  # ID возврата в платёжной системе
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
