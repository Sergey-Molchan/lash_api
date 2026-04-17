import uuid
import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Booking, Payment, Refund

router = APIRouter(prefix="/api/payment", tags=["payment"])

# Флаг для переключения между заглушкой и реальной оплатой
USE_REAL_PAYMENT = os.getenv("USE_REAL_PAYMENT", "False").lower() == "true"

if USE_REAL_PAYMENT:
    from yookassa import Configuration, Payment as YKPayment
    Configuration.account_id = os.getenv('YK_SHOP_ID')
    Configuration.secret_key = os.getenv('YK_SECRET_KEY')

@router.get("/sbp/{booking_id}")
async def get_sbp_payment(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Запись не найдена")
    
    existing_payment = await db.execute(
        select(Payment).where(Payment.booking_id == booking_id, Payment.status.in_(['paid', 'pending']))
    )
    existing = existing_payment.scalar_one_or_none()
    if existing and existing.status == 'paid':
        return {"error": "Это бронирование уже оплачено", "payment_status": "paid"}
    
    if USE_REAL_PAYMENT:
        try:
            idempotence_key = str(uuid.uuid4())
            payment_data = {
                "amount": {"value": "300.00", "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": "https://ваш-сайт.ru/success"},
                "capture": True,
                "description": f"Предоплата за услугу {booking.service_type}",
                "metadata": {"booking_id": booking_id}
            }
            yk_payment = YKPayment.create(payment_data, idempotence_key)
            
            db_payment = Payment(
                booking_id=booking_id,
                payment_id=yk_payment.id,
                amount=300,
                status="pending",
                payment_method="sbp",
                payment_data=json.dumps({"payment_url": yk_payment.confirmation.confirmation_url})
            )
            db.add(db_payment)
            await db.commit()
            
            return {
                "booking_id": booking_id,
                "payment_id": db_payment.id,
                "amount": 300,
                "description": f"Предоплата за {booking.service_type}",
                "payment_url": yk_payment.confirmation.confirmation_url,
                "status": "pending"
            }
        except Exception as e:
            raise HTTPException(400, f"Ошибка создания платежа: {str(e)}")
    else:
        db_payment = Payment(
            booking_id=booking_id,
            payment_id=f"test_{uuid.uuid4().hex[:8]}",
            amount=300,
            status="pending",
            payment_method="sbp"
        )
        db.add(db_payment)
        await db.commit()
        
        return {
            "booking_id": booking_id,
            "payment_id": db_payment.id,
            "amount": 300,
            "description": f"Предоплата за {booking.service_type}",
            "qr_code": f"https://qr.nspk.ru/test_{booking_id}.png",
            "payment_url": f"https://sbp.test/pay/{booking_id}",
            "status": "pending",
            "is_test": True
        }

@router.post("/webhook/sbp")
async def sbp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    booking_id = data.get("booking_id")
    status = data.get("status")
    payment_id = data.get("payment_id")
    
    if payment_id:
        result = await db.execute(select(Payment).where(Payment.payment_id == payment_id))
    else:
        result = await db.execute(select(Payment).where(Payment.booking_id == booking_id))
    
    payment = result.scalar_one_or_none()
    
    if USE_REAL_PAYMENT and status == "succeeded":
        if payment:
            payment.status = "paid"
            payment.paid_at = datetime.now()
            booking = await db.get(Booking, booking_id)
            if booking:
                booking.status = "confirmed"
                booking.paid = True
            await db.commit()
    elif status == "success" and payment:
        payment.status = "paid"
        payment.paid_at = datetime.now()
        booking = await db.get(Booking, booking_id)
        if booking:
            booking.status = "confirmed"
            booking.paid = True
        await db.commit()
    
    return {"ok": True}

@router.post("/refund/{booking_id}")
async def refund_payment(booking_id: int, reason: str = None, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Бронирование не найдено")
    
    if not booking.paid:
        raise HTTPException(400, "Бронирование не оплачено, возврат невозможен")
    
    result = await db.execute(select(Payment).where(Payment.booking_id == booking_id, Payment.status == "paid"))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Платёж не найден")
    
    if USE_REAL_PAYMENT and payment.payment_id and not payment.payment_id.startswith("test_"):
        try:
            from yookassa import Refund as YKRefund
            refund = YKRefund.create({
                "payment_id": payment.payment_id,
                "amount": {"value": str(payment.amount), "currency": "RUB"}
            })
            refund_id = refund.id
            refund_status = refund.status
        except Exception as e:
            raise HTTPException(400, f"Ошибка возврата средств: {str(e)}")
    else:
        refund_id = f"refund_test_{uuid.uuid4().hex[:8]}"
        refund_status = "succeeded"
    
    db_refund = Refund(
        payment_id=payment.id,
        booking_id=booking_id,
        amount=payment.amount,
        reason=reason,
        status="completed" if refund_status == "succeeded" else "pending",
        refund_id=refund_id,
        completed_at=datetime.now() if refund_status == "succeeded" else None
    )
    db.add(db_refund)
    
    payment.status = "refunded"
    payment.refunded_at = datetime.now()
    booking.status = "cancelled"
    booking.paid = False
    
    await db.commit()
    
    return {
        "ok": True,
        "booking_id": booking_id,
        "refund_amount": payment.amount,
        "refund_id": refund_id,
        "status": refund_status
    }

@router.get("/status/{booking_id}")
async def get_payment_status(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Бронирование не найдено")
    
    result = await db.execute(select(Payment).where(Payment.booking_id == booking_id))
    payment = result.scalar_one_or_none()
    
    if not payment:
        return {"booking_id": booking_id, "paid": False, "status": "no_payment"}
    
    return {
        "booking_id": booking_id,
        "paid": booking.paid,
        "payment_status": payment.status,
        "amount": payment.amount,
        "paid_at": payment.paid_at,
        "refunded_at": payment.refunded_at
    }

@router.get("/history")
async def get_payment_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).order_by(Payment.created_at.desc()))
    payments = result.scalars().all()
    
    history = []
    for p in payments:
        booking = await db.get(Booking, p.booking_id)
        history.append({
            "payment_id": p.id,
            "booking_id": p.booking_id,
            "client_name": booking.client_name if booking else "Unknown",
            "client_phone": booking.client_phone if booking else "Unknown",
            "amount": p.amount,
            "status": p.status,
            "paid_at": p.paid_at,
            "created_at": p.created_at
        })
    return history
