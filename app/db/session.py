from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger("app")

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    logger.info("Opening new database session...")
    async with SessionLocal() as session:
        try:
            yield session
            logger.info("Database session yielding...")
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
            logger.info("Database session closed.")
