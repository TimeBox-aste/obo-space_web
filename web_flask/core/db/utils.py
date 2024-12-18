from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from core.db.models import UserData, Base, Statuses
from settings import DATABASE_URL, ASYNC_DATABASE_URL
from core.connector.postgresql_connector import PostgreSQLConnector, db_operation


def create_database(engine_url):
    """Create the database and tables based on the models."""
    engine = create_engine(engine_url)
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    return Session

def init_db(database_url):
    """Initialize database and return session"""
    Session = create_database(database_url)
    
    # Create default statuses if they don't exist
    session = Session()
    try:
        default_statuses = [
            {'name': 'pending', 'description': 'Notification is pending'},
            {'name': 'sent', 'description': 'Notification was sent successfully'},
            {'name': 'failed', 'description': 'Notification failed to send'}
        ]
        
        for status in default_statuses:
            existing = session.query(Statuses).filter_by(name=status['name']).first()
            if not existing:
                session.add(Statuses(**status))
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        
    return Session

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