"""
Base Database Model

Provides common functionality for all database models.
"""

import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr

logger = logging.getLogger(__name__)

Base = declarative_base()


async def init_db() -> None:
    """
    Create all database tables that are registered against ``Base``.

    Called once during application startup. Uses the ``DATABASE_URL``
    setting if available; falls back to SQLite so startup never fails
    in a development environment without PostgreSQL.
    """
    import os
    from sqlalchemy.pool import StaticPool

    raw_url: str = os.environ.get(
        "DATABASE_URL", "sqlite+aiosqlite:///./kopitar.db"
    )

    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("sqlite://") and not raw_url.startswith("sqlite+aiosqlite://"):
        raw_url = raw_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    is_sqlite = raw_url.startswith("sqlite")
    engine_kwargs = (
        {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
        if is_sqlite
        else {"pool_pre_ping": True}
    )

    try:
        engine = create_async_engine(raw_url, **engine_kwargs)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        logger.info("Database initialised (%s)", raw_url.split("@")[-1])
    except Exception:
        logger.warning("init_db failed — tables may not exist", exc_info=True)


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """
    
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now()
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        server_onupdate=func.now()
    )


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model with common fields.
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    @declared_attr
    def __tablename__(cls):
        """
        Automatically generate table name from class name.
        Convert CamelCase to snake_case.
        """
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def __repr__(self):
        """
        String representation showing primary key.
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self, include_relationships=False):
        """
        Convert model instance to dictionary.
        
        Args:
            include_relationships: Whether to include relationship fields
            
        Returns:
            dict: Model data as dictionary
        """
        result = {}
        
        # Include basic columns
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        
        # Include relationships if requested
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                value = getattr(self, relationship.key)
                if value is not None:
                    if hasattr(value, '__iter__') and not isinstance(value, str):
                        # Collection relationship
                        result[relationship.key] = [
                            item.to_dict() if hasattr(item, 'to_dict') else str(item)
                            for item in value
                        ]
                    else:
                        # Single relationship
                        result[relationship.key] = (
                            value.to_dict() if hasattr(value, 'to_dict') else str(value)
                        )
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        """
        Create model instance from dictionary.
        
        Args:
            data: Dictionary with model data
            
        Returns:
            Model instance
        """
        # Filter data to only include valid columns
        valid_columns = {column.name for column in cls.__table__.columns}
        filtered_data = {
            key: value for key, value in data.items()
            if key in valid_columns and key not in ('id', 'created_at', 'updated_at')
        }
        
        return cls(**filtered_data)
    
    def update_from_dict(self, data):
        """
        Update model instance from dictionary.
        
        Args:
            data: Dictionary with updated data
        """
        valid_columns = {column.name for column in self.__table__.columns}
        
        for key, value in data.items():
            if key in valid_columns and key not in ('id', 'created_at'):
                setattr(self, key, value)


class AuditMixin:
    """
    Mixin to add audit fields for tracking data changes.
    """
    
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    
    # Source of data (e.g., 'nhl_api', 'manual_entry', 'calculated')
    data_source = Column(
        String(50),
        nullable=False,
        default='nhl_api'
    )
    
    # Version for tracking schema changes
    data_version = Column(Integer, nullable=False, default=1)


class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality.
    """
    
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    
    @property
    def is_deleted(self):
        """Check if record is soft deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self, user_id=None):
        """Soft delete the record."""
        self.deleted_at = datetime.utcnow()
        if user_id:
            self.deleted_by = user_id
    
    def restore(self):
        """Restore a soft deleted record."""
        self.deleted_at = None
        self.deleted_by = None