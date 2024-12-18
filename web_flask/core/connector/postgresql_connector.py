from typing import Optional, Any, Union
import asyncio
from functools import wraps
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, insert, update, delete

from settings import DATABASE_URL, ASYNC_DATABASE_URL
from core.db.models import UserData

class PostgreSQLConnector:
    """PostgreSQL connector supporting both sync and async operations"""
    
    def __init__(self):
        self._engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        self._async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
        
        self._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )
        
        self._AsyncSessionLocal = async_sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @contextmanager
    def get_db(self) -> Session:
        """Synchronous database session context manager"""
        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    async def get_async_db(self) -> AsyncSession:
        """Asynchronous database session context manager"""
        async with self._AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    def execute_sync(self, query: Any) -> Any:
        """Execute synchronous database query"""
        with self.get_db() as db:
            result = db.execute(query)
            return result

    async def execute_async(self, query: Any) -> Any:
        """Execute asynchronous database query"""
        async with self.get_async_db() as db:
            result = await db.execute(query)
            return result

    def dispose(self):
        """Dispose synchronous engine"""
        self._engine.dispose()

    async def dispose_async(self):
        """Dispose asynchronous engine"""
        await self._async_engine.dispose()

def db_operation(is_async: bool = False):
    """Decorator for database operations"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            connector = PostgreSQLConnector()
            try:
                async with connector.get_async_db() as session:
                    kwargs['session'] = session
                    result = await func(*args, **kwargs)
                    return result
            finally:
                await connector.dispose_async()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            connector = PostgreSQLConnector()
            try:
                with connector.get_db() as session:
                    kwargs['session'] = session
                    return func(*args, **kwargs)
            finally:
                connector.dispose()

        return async_wrapper if is_async else sync_wrapper
    return decorator

# Usage examples:
@db_operation(is_async=False)
def get_user_by_id(user_id: int, session: Session) -> Optional[Any]:
    """Example of synchronous database operation"""
    return session.query(UserData).filter(UserData.id == user_id).first()

@db_operation(is_async=True)
async def get_user_by_email(email: str, session: AsyncSession) -> Optional[Any]:
    """Example of asynchronous database operation"""
    result = await session.execute(
        select(UserData).filter(UserData.email == email)
    )
    return result.scalar_one_or_none()

# Singleton instance
db = PostgreSQLConnector()
