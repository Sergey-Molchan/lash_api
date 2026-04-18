from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.database import init_db
from app.routers import admin, client, calendar, hours, prices, content, gallery, comments, finance
import os

app = FastAPI(title="Lash Studio API")

os.makedirs("app/static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(client.router)
app.include_router(calendar.router)
app.include_router(hours.router)
app.include_router(prices.router)
app.include_router(content.router)
app.include_router(gallery.router)
app.include_router(comments.router)
app.include_router(finance.router)

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

@app.get("/health")
async def health():
    return {"status": "healthy"}