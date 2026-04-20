from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Price
from pydantic import BaseModel

router = APIRouter(prefix="/api/prices", tags=["prices"])

class PriceUpdate(BaseModel):
    service: str
    price: int

@router.get("/")
async def get_prices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Price))
    prices = {p.service: p.price for p in result.scalars().all()}
    return {
        "lashes_1d": prices.get("lashes_1d", 2500),
        "lashes_2d": prices.get("lashes_2d", 3000),
        "lashes_3d": prices.get("lashes_3d", 3500),
        "brows": prices.get("brows", 2000),
        "complex": prices.get("complex", 3800),
        "deposit": prices.get("deposit", 300)
    }

@router.post("/")
async def update_price(update: PriceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Price).where(Price.service == update.service))
    price = result.scalar_one_or_none()
    if price:
        price.price = update.price
    else:
        price = Price(service=update.service, price=update.price)
        db.add(price)
    await db.commit()
    return {"ok": True}
