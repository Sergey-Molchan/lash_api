from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
from app.database import get_db
from app.models import GalleryImage
from fastapi.responses import Response

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


@router.post("/upload")
async def upload_image(
        file: UploadFile = File(...),
        title: str = Form(None),
        description: str = Form(None),
        db: AsyncSession = Depends(get_db)
):
    """Загрузка фото в БД"""
    contents = await file.read()

    image = GalleryImage(
        title=title,
        description=description,
        image_data=contents,
        filename=file.filename,
        content_type=file.content_type,
        created_at=datetime.now()
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return {"ok": True, "id": image.id, "url": f"/api/gallery/image/{image.id}"}


@router.get("/image/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    """Получение фото из БД"""
    result = await db.execute(select(GalleryImage).where(GalleryImage.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, "Image not found")
    return Response(content=image.image_data, media_type=image.content_type)


@router.get("/")
async def get_gallery(db: AsyncSession = Depends(get_db)):
    """Список фото для галереи"""
    result = await db.execute(select(GalleryImage).order_by(GalleryImage.id.desc()))
    images = result.scalars().all()
    return [
        {
            "id": img.id,
            "title": img.title,
            "description": img.description,
            "url": f"/api/gallery/image/{img.id}",
            "created_at": img.created_at
        }
        for img in images
    ]


@router.delete("/{image_id}")
async def delete_gallery_image(image_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(GalleryImage).where(GalleryImage.id == image_id))
    await db.commit()
    return {"ok": True}