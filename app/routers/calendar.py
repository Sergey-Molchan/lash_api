from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime
from app.database import get_db
from app.models import Booking, WorkingHours

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

MONTHS_RU = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь',
             'Декабрь']


@router.get("/data", response_class=HTMLResponse)
async def get_calendar_data(db: AsyncSession = Depends(get_db), year: int = None, month: int = None):
    now = datetime.now()
    y = year if year else now.year
    m = month if month else now.month
    start = date(y, m, 1)
    if m == 12:
        end = date(y + 1, 1, 1)
    else:
        end = date(y, m + 1, 1)

    bookings_result = await db.execute(select(Booking).where(Booking.booking_date >= start, Booking.booking_date < end))
    bookings = bookings_result.scalars().all()
    wh_result = await db.execute(select(WorkingHours).where(WorkingHours.date >= start, WorkingHours.date < end))
    days_off = {wh.date.strftime('%Y-%m-%d') for wh in wh_result.scalars().all() if wh.is_day_off}

    bookings_by_day = {}
    for b in bookings:
        key = b.booking_date.strftime('%Y-%m-%d')
        bookings_by_day.setdefault(key, []).append(b)

    html = f'<div class="calendar-container"><div class="calendar-header"><h2>{MONTHS_RU[m - 1]} {y}</h2><div class="calendar-nav"><button onclick="changeMonth(-1)">◀</button><button onclick="changeMonth(1)">▶</button></div></div><div class="calendar-grid">'
    for wd in ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']:
        html += f'<div class="calendar-weekday">{wd}</div>'
    first = (start.weekday() + 6) % 7
    for _ in range(first):
        html += '<div class="calendar-day"></div>'
    for d in range(1, 32):
        try:
            cur = date(y, m, d)
        except:
            break
        ds = cur.strftime('%Y-%m-%d')
        off = ds in days_off
        day_bookings = bookings_by_day.get(ds, [])
        html += f'<div class="calendar-day {"off" if off else ""}" data-date="{ds}"><div class="day-number">{d}</div>'
        for b in day_bookings:
            status_icon = '✅' if b.status == 'confirmed' else '⏳' if b.status == 'pending' else '❌'
            html += f'<div class="booking-item {b.status}" onclick="showBookingDetail({b.id})"><span class="booking-time">{b.booking_date.strftime("%H:%M")}</span><span>{b.client_name[:12]}</span><span>{status_icon}</span></div>'
        html += f'<div class="day-actions"><button class="btn-day-off" onclick="toggleDayOff(\'{ds}\')">{"❌ Выходной" if off else "✅ Рабочий"}</button><button class="btn-hours" onclick="editDayHours(\'{ds}\')">⏰ Часы</button></div></div>'
    html += '</div></div>'
    return HTMLResponse(content=html)