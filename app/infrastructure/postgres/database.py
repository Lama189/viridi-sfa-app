from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

settings = get_settings()
db_url = settings.database_url or "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(db_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()
