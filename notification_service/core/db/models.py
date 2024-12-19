from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, event, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship, DeclarativeBase  # declarative_base,
from sqlalchemy.ext.declarative import declared_attr

class Base(AsyncAttrs, DeclarativeBase):
    pass

class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class BaseMixin:
    """Base mixin for common model attributes"""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

class UserData(Base, BaseMixin, TimestampMixin):
    """User data model with enhanced tracking"""
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    copies_shared = relationship('CopyShared', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.email}>"

class CopyShared(Base, BaseMixin, TimestampMixin):
    """Copy shared model with enhanced tracking"""
    id_user = Column(Integer, ForeignKey('userdata.id', ondelete='CASCADE'), nullable=False)
    name_file_uuid = Column(String(255), nullable=False, index=True)
    
    user = relationship('UserData', back_populates='copies_shared')
    notifications = relationship('Notifications', back_populates='copy', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<CopyShared {self.name_file_uuid}>"

class Notifications(Base, BaseMixin):
    """Notifications model with enhanced tracking"""
    id_copy_shared = Column(Integer, ForeignKey('copyshared.id', ondelete='CASCADE'), nullable=False)
    id_status_sending = Column(Integer, ForeignKey('statuses.id'), nullable=False)
    dt_sent = Column(DateTime, default=datetime.now, server_default=func.now(), nullable=False)
    attempts = Column(Integer, default=0, server_default='0', nullable=False)
    max_attempts = Column(Integer, default=3, server_default='3', nullable=False)
    
    copy = relationship('CopyShared', back_populates='notifications')
    status = relationship('Statuses', back_populates='notifications')

    def __repr__(self):
        return f"<Notification {self.uniqueId}>"

class Statuses(Base, BaseMixin):
    """Statuses model for notification states"""
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    
    notifications = relationship('Notifications', back_populates='status')

    def __repr__(self):
        return f"<Status {self.name}>"

# Event listeners for automatic timestamp updates
@event.listens_for(Base, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    if hasattr(target, 'updated_at'):
        target.updated_at = datetime.utcnow()
