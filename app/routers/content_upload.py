from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/api/content-upload", tags=["content-upload"])


@router.post("/")
async def upload_content_image(file: UploadFile = File(...)):
    """Загрузка фото для контента (без сохранения в галерею)"""
    os.makedirs("app/static/uploads", exist_ok=True)

    # Проверяем тип файла
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "Можно загружать только изображения")

    # Генерируем уникальное имя файла
    ext = file.filename.split('.')[-1]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"content_{timestamp}_{abs(hash(file.filename))}.{ext}"
    filepath = f"app/static/uploads/{filename}"

    # Сохраняем файл
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"/static/uploads/{filename}"}