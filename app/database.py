import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Приоритет: DATABASE_URL (Railway) > самосборный URL из переменных
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Собираем из отдельных переменных (локальная разработка)
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB")
    if not all([user, password, db]):
        raise ValueError("Neither DATABASE_URL nor POSTGRES_* variables are set")
    DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

engine = create_async_engine(DATABASE_URL, echo=True)
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ PostgreSQL connected and tables created")