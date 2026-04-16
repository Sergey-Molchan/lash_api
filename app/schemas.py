from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BookingCreate(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=100)
    client_phone: str = Field(..., pattern=r'^\+?[0-9]{10,15}$')
    service_type: str = Field(..., pattern='^(lashes|brows)$')
    booking_date: datetime
    master_id: Optional[int] = None


class BookingResponse(BaseModel):
    id: int
    client_name: str
    client_phone: str
    service_type: str
    booking_date: datetime
    status: str
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class BookingUpdate(BaseModel):
    booking_date: Optional[datetime] = None
    status: Optional[str] = None
    master_id: Optional[int] = None


class PaymentRequest(BaseModel):
    booking_id: int
    payment_method: str = "sbp"  # sbp, card, cash


class PaymentResponse(BaseModel):
    payment_url: str
    booking_id: int
    amount: float
    qr_code: Optional[str] = None