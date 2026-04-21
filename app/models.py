from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, LargeBinary
from datetime import datetime
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    service_type = Column(String(50), nullable=False)
    lashes_volume = Column(String(10), nullable=True)  # 1d, 2d, 3d — только для ресниц
    booking_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")
    amount = Column(Float, default=300.0)
    paid = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
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


class GalleryImage(Base):
    __tablename__ = "gallery_images"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    image_data = Column(LargeBinary, nullable=False)  # ← само фото в БД
    filename = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class HomeImage(Base):
    __tablename__ = "home_images"
    id = Column(Integer, primary_key=True, index=True)
    section = Column(String(50), unique=True, nullable=False)  # 'lashes', 'brows', 'complex'
    image_data = Column(LargeBinary, nullable=False)
    content_type = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)