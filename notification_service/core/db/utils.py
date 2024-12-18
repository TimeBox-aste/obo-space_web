from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from models import UserData
from notification_service.settings import DATABASE_URL, ASYNC_DATABASE_URL
from sqlalchemy.orm import Session
from core.connector.postgresql_connector import db_operation

def create_database(engine_url):
    """Create the database and tables based on the models."""
    engine = create_engine(engine_url)
    Base.metadata.create_all(engine)

def get_session(engine_url):
    """Get a new session for the database."""
    engine = create_engine(engine_url)
    Session = sessionmaker(bind=engine)
    return Session()


# Synchronous usage
@db_operation(is_async=False)
def create_user(user_data: dict, session: Session):
    user = UserData(**user_data)
    session.add(user)
    return user

# Asynchronous usage
@db_operation(is_async=True)
async def get_users_by_status(status: str, session: AsyncSession):
    result = await session.execute(
        select(UserData).filter(UserData.status == status)
    )
    return result.scalars().all()

# # Direct connector usage
# with db.get_db() as session:
#     users = session.query(UserData).all()

# async with db.get_async_db() as session:
#     result = await session.execute(select(UserData))
#     users = result.scalars().all()