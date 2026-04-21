from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from app.routers import content_upload, home_images
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import init_db
from app.routers import admin, client, calendar, hours, prices, content, gallery, comments, finance, notifications
import os

app = FastAPI(title="Lash Studio API")

# Middleware для отключения кэширования API
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Отключаем кэш для всех API запросов
        if request.url.path.startswith("/api/") or request.url.path.startswith("/static/uploads/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

# Создаем папку для загрузок
os.makedirs("app/static/uploads", exist_ok=True)

# Монтируем статику ДО middleware
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ВАЖНО: Убираем HTTPSRedirectMiddleware (он вызывает бесконечный редирект на Cloud Run)
# app.add_middleware(HTTPSRedirectMiddleware)  # ← ЗАКОММЕНТИРОВАНО!

# Добавляем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.lash-saundra.online", "https://lash-saundra.online", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для отключения кэша
app.add_middleware(NoCacheMiddleware)

# Подключаем роутеры
app.include_router(admin.router)
app.include_router(client.router)
app.include_router(calendar.router)
app.include_router(hours.router)
app.include_router(prices.router)
app.include_router(content.router)
app.include_router(gallery.router)
app.include_router(comments.router)
app.include_router(finance.router)
app.include_router(notifications.router)
app.include_router(content_upload.router)
app.include_router(home_images.router)

def read_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/", response_class=HTMLResponse)
async def home_page():
    return read_html("app/templates/client/index.html")

@app.get("/booking", response_class=HTMLResponse)
async def booking_page():
    return read_html("app/templates/client/booking.html")

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page():
    return read_html("app/templates/client/portfolio.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/admin", status_code=303)

@app.get("/admin/hours", response_class=HTMLResponse)
async def hours_page():
    return read_html("app/templates/hours.html")

@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ App started")

@app.on_event("shutdown")
async def shutdown():
    print("👋 App shutdown")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/add-to-home", response_class=HTMLResponse)
async def add_to_home_page():
    return read_html("app/templates/add-to-home.html")

@app.get("/thankyou", response_class=HTMLResponse)
async def thankyou_page():
    return read_html("app/templates/client/thankyou.html")

# Диагностический эндпоинт для проверки фото
@app.get("/debug/photos")
async def debug_photos():
    import os
    uploads_dir = "app/static/uploads"
    files = []
    if os.path.exists(uploads_dir):
        files = [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
    return {
        "uploads_exists": os.path.exists(uploads_dir),
        "uploads_path": os.path.abspath(uploads_dir),
        "files": files,
        "static_mounted": True
    }