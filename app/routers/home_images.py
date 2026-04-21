from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models import HomeImage
from fastapi.responses import Response

router = APIRouter(prefix="/api/home-images", tags=["home-images"])


@router.post("/upload/{section}")
async def upload_home_image(
        section: str,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    """Загрузка фото для главной страницы"""
    if section not in ['lashes', 'brows', 'complex']:
        raise HTTPException(400, "Неверная секция")

    contents = await file.read()

    # Проверяем, есть ли уже фото для этой секции
    result = await db.execute(select(HomeImage).where(HomeImage.section == section))
    existing = result.scalar_one_or_none()

    if existing:
        existing.image_data = contents
        existing.content_type = file.content_type
        existing.updated_at = datetime.now()
    else:
        home_image = HomeImage(
            section=section,
            image_data=contents,
            content_type=file.content_type
        )
        db.add(home_image)

    await db.commit()
    return {"ok": True, "url": f"/api/home-images/{section}"}


@router.get("/{section}")
async def get_home_image(section: str, db: AsyncSession = Depends(get_db)):
    """Получение фото для главной страницы"""
    result = await db.execute(select(HomeImage).where(HomeImage.section == section))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, "Image not found")
    return Response(content=image.image_data, media_type=image.content_type)


@router.get("/")
async def get_all_home_images(db: AsyncSession = Depends(get_db)):
    """Получение всех фото для главной страницы"""
    result = await db.execute(select(HomeImage))
    images = result.scalars().all()
    return {
        img.section: f"/api/home-images/{img.section}" for img in images
    }