from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from datetime import datetime

# Используем SQLite — не нужны переменные окружения
DATABASE_URL = "sqlite+aiosqlite:///./lashes.db"

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Твои модели (скопируй их из старого файла)
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
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

# Добавь сюда остальные модели (WorkingHours, DayHours, Price, SiteContent, GalleryImage, Comment)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ SQLite connected")