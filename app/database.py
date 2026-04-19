import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# ========== УМНАЯ КОНФИГУРАЦИЯ БД ==========
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Пробуем собрать из отдельных переменных (локальный .env)
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    if POSTGRES_USER and POSTGRES_PASSWORD and POSTGRES_DB:
        DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    else:
        # SQLite для локальной разработки
        DATABASE_URL = "sqlite+aiosqlite:///./lashes.db"

# ========== НАСТРОЙКИ В ЗАВИСИМОСТИ ОТ ТИПА БД ==========
is_sqlite = DATABASE_URL.startswith("sqlite")
is_postgres = "postgresql" in DATABASE_URL

# Базовые настройки
engine_kwargs = {
    "echo": os.getenv("DEBUG", "False") == "True",
}

# Настройки для SQLite
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# Настройки для PostgreSQL
if is_postgres:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["connect_args"] = {
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }

# ========== СОЗДАНИЕ ENGINE ==========
engine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С БД ==========
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Инициализация БД (создание таблиц)"""
    from app.models import Base as ModelsBase  # Импортируем Base из models
    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)

        db_type = "PostgreSQL" if is_postgres else "SQLite"
        print(f"✅ {db_type} connected: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")