from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import SiteContent

router = APIRouter(prefix="/api/content", tags=["content"])

@router.get("/")
async def get_site_content(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SiteContent))
    content = {c.section: c.content for c in result.scalars().all()}
    return {
        "hero_title": content.get("hero_title", "✨ Идеальный взгляд начинается здесь"),
        "hero_text": content.get("hero_text", "Наращивание ресниц и ламинирование бровей в Адлере"),
        "about": content.get("about", "Lash Studio — уютная студия красоты в Адлере"),
        "address": content.get("address", "📍 улица Голубые Дали, 78, Адлер")
    }

@router.post("/")
async def update_site_content(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    section = data.get("section")
    new_content = data.get("content")
    result = await db.execute(select(SiteContent).where(SiteContent.section == section))
    item = result.scalar_one_or_none()
    if item:
        item.content = new_content
    else:
        item = SiteContent(section=section, content=new_content)
        db.add(item)
    await db.commit()
    return {"ok": True}