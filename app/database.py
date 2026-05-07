import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

# For prototype, use SQLite if Postgres URL is not provided, 
# but user requested Postgres. I'll use a placeholder URL.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/clinic_db")

Base = declarative_base()

class CallLog(Base):
    __tablename__ = "call_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(String)
    ai_response = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    # Only use this if you have postgres running
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    pass

async def log_call(user_query: str, ai_response: str):
    async with async_session() as session:
        log = CallLog(user_query=user_query, ai_response=ai_response)
        session.add(log)
        await session.commit()
