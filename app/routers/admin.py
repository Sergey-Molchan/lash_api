from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.admin_auth import create_session, verify_session, logout
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.models import Booking, WorkingHours, Comment
from typing import List, Optional
from datetime import date, datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><title>Вход в админ-панель</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}.login-container{background:white;padding:40px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);width:400px}h1{text-align:center;margin-bottom:30px;color:#333}input{width:100%;padding:12px;margin-bottom:20px;border:2px solid #e0e0e0;border-radius:10px;font-size:16px}button{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:10px;font-size:16px;font-weight:bold;cursor:pointer}</style></head>
<body><div class="login-container"><h1>🔐 Вход в админ-панель</h1>
<form method="post" action="/api/admin/login"><input type="text" name="username" placeholder="Логин" required autofocus><input type="password" name="password" placeholder="Пароль" required><button type="submit">Войти</button></form></div></body></html>'''


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return HTMLResponse(content=LOGIN_HTML)


@router.post("/login")
async def admin_login(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        return RedirectResponse(url="/api/admin/login", status_code=303)

    token = create_session()
    response = RedirectResponse(url="/api/admin", status_code=303)
    response.set_cookie(key="admin_token", value=token, httponly=True, max_age=86400)
    return response


@router.get("/logout")
async def admin_logout(request: Request):
    token = request.cookies.get("admin_token")
    logout(token)
    response = RedirectResponse(url="/api/admin/login", status_code=303)
    response.delete_cookie("admin_token")
    return response


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    token = request.cookies.get("admin_token")
    if not token or not verify_session(token):
        return RedirectResponse(url="/api/admin/login", status_code=303)
    with open("app/templates/admin/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


class BookingResponse(BaseModel):
    id: int
    client_name: str
    client_phone: str
    service_type: str
    booking_date: datetime
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/bookings", response_model=List[BookingResponse])
async def get_bookings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).order_by(Booking.booking_date.desc()))
    return result.scalars().all()


@router.get("/booking/{booking_id}")
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    return {
        "id": booking.id,
        "client_name": booking.client_name,
        "client_phone": booking.client_phone,
        "service_type": booking.service_type,
        "booking_date": booking.booking_date.isoformat(),
        "status": booking.status,
        "notes": booking.notes
    }


@router.post("/confirm/{booking_id}")
async def confirm_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if booking:
        booking.status = "confirmed"
        await db.commit()
    return {"ok": True}


@router.post("/cancel/{booking_id}")
async def cancel_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if booking:
        booking.status = "cancelled"
        await db.commit()
    return {"ok": True}


@router.delete("/booking/{booking_id}")
async def delete_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    await db.delete(booking)
    await db.commit()
    return {"ok": True}


@router.post("/toggle-day-off/{date_str}")
async def toggle_day_off(date_str: str, db: AsyncSession = Depends(get_db)):
    target_date = date.fromisoformat(date_str)
    result = await db.execute(select(WorkingHours).where(WorkingHours.date == target_date))
    day_off = result.scalar_one_or_none()
    if day_off:
        await db.delete(day_off)
        await db.commit()
        return {"ok": True, "is_day_off": False}
    else:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        bookings = await db.execute(select(Booking).where(Booking.booking_date >= start, Booking.booking_date <= end))
        bookings_list = bookings.scalars().all()
        if bookings_list:
            return {
                "warning": True,
                "message": f"На этот день есть {len(bookings_list)} записей. Они будут удалены!",
                "bookings": [{"id": b.id, "client_name": b.client_name, "time": b.booking_date.strftime("%H:%M")} for b
                             in bookings_list]
            }
        else:
            db.add(WorkingHours(date=target_date, is_day_off=True))
            await db.commit()
            return {"ok": True, "is_day_off": True}


@router.post("/confirm-day-off/{date_str}")
async def confirm_day_off(date_str: str, db: AsyncSession = Depends(get_db)):
    target_date = date.fromisoformat(date_str)
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    await db.execute(delete(Booking).where(Booking.booking_date >= start, Booking.booking_date <= end))
    existing = await db.execute(select(WorkingHours).where(WorkingHours.date == target_date))
    old = existing.scalar_one_or_none()
    if old:
        await db.delete(old)
    db.add(WorkingHours(date=target_date, is_day_off=True))
    await db.commit()
    return {"ok": True}


class CommentResponse(BaseModel):
    id: int
    client_name: str
    client_phone: str
    rating: int
    text: str
    emoji: str
    created_at: datetime
    is_approved: bool

    class Config:
        from_attributes = True


@router.get("/comments/pending", response_model=List[CommentResponse])
async def get_pending_comments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Comment).where(Comment.is_approved == False).order_by(Comment.created_at.desc()))
    return result.scalars().all()


@router.post("/comments/approve/{comment_id}")
async def approve_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(404, "Комментарий не найден")
    comment.is_approved = True
    await db.commit()
    return {"ok": True}


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(404, "Комментарий не найден")
    await db.delete(comment)
    await db.commit()
    return {"ok": True}


@router.post("/manual-booking")
async def manual_booking(booking_data: dict, db: AsyncSession = Depends(get_db)):
    """Ручное добавление записи админом (через страницу управления часами)"""
    from datetime import datetime, timedelta
    from sqlalchemy import select

    booking_date = datetime.fromisoformat(booking_data.get("booking_date"))

    if booking_date <= datetime.now():
        raise HTTPException(400, "Дата должна быть в будущем")

    # Длительность услуг
    SERVICE_DURATION = {
        "lashes": 2.5,
        "brows": 1.0,
        "complex": 3.0
    }
    duration = SERVICE_DURATION.get(booking_data.get("service_type"), 1.0)
    booking_end = booking_date + timedelta(hours=duration)

    # Проверяем пересечения с существующими записями
    existing_bookings = await db.execute(
        select(Booking).where(
            Booking.booking_date >= booking_date - timedelta(hours=3),
            Booking.booking_date <= booking_end,
            Booking.status.in_(['pending', 'confirmed'])
        )
    )
    for existing in existing_bookings.scalars().all():
        existing_end = existing.booking_date + timedelta(hours=SERVICE_DURATION.get(existing.service_type, 1.0))
        if not (booking_date >= existing_end or booking_end <= existing.booking_date):
            raise HTTPException(400, "Это время уже занято")

    db_booking = Booking(
        client_name=booking_data.get("client_name"),
        client_phone=booking_data.get("client_phone"),
        service_type=booking_data.get("service_type"),
        booking_date=booking_date,
        status="confirmed",  # админ подтверждает сразу
        notes=booking_data.get("comment", "")
    )
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)
    return {"ok": True, "id": db_booking.id}


@router.get("/bookings", response_model=List[BookingResponse])
async def get_bookings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).order_by(Booking.booking_date.desc()))
    return result.scalars().all()