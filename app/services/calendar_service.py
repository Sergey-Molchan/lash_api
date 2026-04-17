from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models import Booking, WorkingHours, TimeSlot

class CalendarService:
    
    @staticmethod
    async def get_month_bookings(db: AsyncSession, year: int, month: int):
        """Получить все записи за месяц"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        result = await db.execute(
            select(Booking).where(
                Booking.booking_date >= start_date,
                Booking.booking_date < end_date
            ).order_by(Booking.booking_date)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_days_off(db: AsyncSession, year: int, month: int):
        """Получить выходные дни за месяц"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        result = await db.execute(
            select(WorkingHours).where(
                WorkingHours.date >= start_date,
                WorkingHours.date < end_date,
                WorkingHours.is_day_off == True
            )
        )
        return {wh.date.isoformat() for wh in result.scalars().all()}
    
    @staticmethod
    async def toggle_day_off(db: AsyncSession, target_date: date):
        """Включить/выключить выходной день"""
        result = await db.execute(
            select(WorkingHours).where(WorkingHours.date == target_date)
        )
        day_off = result.scalar_one_or_none()
        
        if day_off:
            await db.delete(day_off)
        else:
            new_day_off = WorkingHours(date=target_date, is_day_off=True)
            db.add(new_day_off)
            # Удаляем все записи на этот день
            await db.execute(
                delete(Booking).where(
                    Booking.booking_date >= target_date,
                    Booking.booking_date < target_date + timedelta(days=1)
                )
            )
        
        await db.commit()
        return not bool(day_off)
