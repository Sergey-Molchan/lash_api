import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
from app.database import get_db
from app.models import GalleryImage

router = APIRouter(prefix="/api/gallery", tags=["gallery"])

@router.get("/")
async def get_gallery(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GalleryImage).order_by(GalleryImage.id))
    return result.scalars().all()

@router.post("/upload")
async def upload_image(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    os.makedirs("app/static/uploads", exist_ok=True)
    ext = file.filename.split('.')[-1]
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{abs(hash(file.filename))}.{ext}"
    filepath = f"app/static/uploads/{filename}"
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    image = GalleryImage(url=f"/static/uploads/{filename}", title=file.filename)
    db.add(image)
    await db.commit()
    return {"ok": True, "url": f"/static/uploads/{filename}"}

@router.delete("/{image_id}")
async def delete_gallery_image(image_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(GalleryImage).where(GalleryImage.id == image_id))
    await db.commit()
    return {"ok": True}