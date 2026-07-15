from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


def build_worker_session_maker():
    worker_engine = create_async_engine(settings.database_url, echo=settings.debug)
    return async_sessionmaker(worker_engine, expire_on_commit=False), worker_engine