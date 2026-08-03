from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

settings = get_settings()
db_url = settings.database_url or "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(db_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


def create_session_factory(
    database_url: str | None = None,
    echo: bool | None = None,
) -> async_sessionmaker[AsyncSession]:
    url = database_url or settings.database_url or "sqlite+aiosqlite:///:memory:"
    debug_flag = settings.debug if echo is None else echo
    session_engine = create_async_engine(url, echo=debug_flag)
    return async_sessionmaker(session_engine, expire_on_commit=False)


def build_worker_session_maker():
    worker_engine = create_async_engine(settings.database_url, echo=settings.debug)
    return async_sessionmaker(worker_engine, expire_on_commit=False), worker_engine