import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Берём готовый DATABASE_URL от Railway
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Для локальной разработки — SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./lashes.db"

# Простой engine без лишних параметров
engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

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
    from app.models import Base as ModelsBase
    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)
        print("✅ Database connected")