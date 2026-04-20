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
        "address": content.get("address", "📍 улица Голубые Дали, 78, Адлер"),
        "service_lashes_img": content.get("service_lashes_img",
                                          "https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?w=400"),
        "service_brows_img": content.get("service_brows_img",
                                         "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=400"),
        "service_complex_img": content.get("service_complex_img",
                                           "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=400")
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