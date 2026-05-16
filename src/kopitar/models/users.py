"""
User and Authentication Database Models

Models for user management and session tracking.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timedelta
import uuid
import enum
import hashlib

from .base import BaseModel, AuditMixin, SoftDeleteMixin


class UserRole(enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    ANALYST = "analyst"
    COACH = "coach"
    SCOUT = "scout"
    VIEWER = "viewer"
    API_USER = "api_user"


class SubscriptionTier(enum.Enum):
    """Subscription tier enumeration."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    TEAM = "team"


class User(BaseModel, AuditMixin, SoftDeleteMixin):
    """
    User model for authentication and authorization.
    """
    
    __tablename__ = 'users'
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Personal Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True)
    
    # Authorization
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    subscription_tier = Column(Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    
    # Account Status
    active = Column(Boolean, nullable=False, default=True)
    verified = Column(Boolean, nullable=False, default=False)
    locked = Column(Boolean, nullable=False, default=False)
    
    # Verification
    verification_token = Column(String(255), nullable=True)
    verification_sent_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Password Reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Login Tracking
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, nullable=False, default=0)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # API Access
    api_key = Column(String(255), nullable=True, unique=True)
    api_key_created = Column(DateTime, nullable=True)
    api_calls_today = Column(Integer, nullable=False, default=0)
    api_quota_daily = Column(Integer, nullable=False, default=1000)
    
    # Team Association
    organization = Column(String(200), nullable=True)
    team_affiliations = Column(JSONB, nullable=True)  # Array of team IDs user can access
    
    # Preferences
    timezone = Column(String(50), nullable=False, default='UTC')
    dashboard_layout = Column(JSONB, nullable=True)
    notification_preferences = Column(JSONB, nullable=True)
    
    # Subscription Details
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Usage Analytics
    total_queries = Column(Integer, nullable=False, default=0)
    favorite_players = Column(JSONB, nullable=True)  # Array of player IDs
    favorite_teams = Column(JSONB, nullable=True)  # Array of team IDs
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role.value}')>"
    
    @property
    def full_name(self):
        """Get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username
    
    @property
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_premium(self):
        """Check if user has premium subscription."""
        return self.subscription_tier in [SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE]
    
    @property
    def subscription_active(self):
        """Check if subscription is currently active."""
        if not self.subscription_end:
            return False
        return datetime.utcnow() <= self.subscription_end
    
    @property
    def can_access_api(self):
        """Check if user can access API."""
        return self.api_key is not None and self.active and not self.locked
    
    @property
    def api_quota_remaining(self):
        """Get remaining API quota for today."""
        return max(0, self.api_quota_daily - self.api_calls_today)
    
    def generate_api_key(self):
        """Generate a new API key."""
        key_data = f"{self.id}:{self.email}:{datetime.utcnow().isoformat()}:{uuid.uuid4()}"
        self.api_key = hashlib.sha256(key_data.encode()).hexdigest()
        self.api_key_created = datetime.utcnow()
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        # This would use proper password hashing (bcrypt, etc.)
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
    
    def set_password(self, password):
        """Set password hash."""
        # This would use proper password hashing (bcrypt, etc.)
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def can_access_team(self, team_id):
        """Check if user can access specific team data."""
        if self.is_admin:
            return True
        
        if not self.team_affiliations:
            return False
        
        return team_id in self.team_affiliations
    
    def increment_api_usage(self):
        """Increment API usage counter."""
        self.api_calls_today += 1
        self.total_queries += 1
    
    def reset_daily_counters(self):
        """Reset daily usage counters."""
        self.api_calls_today = 0
        self.failed_login_attempts = 0
    
    def lock_account(self, duration_hours=24):
        """Lock user account for specified duration."""
        self.locked = True
        self.locked_until = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def unlock_account(self):
        """Unlock user account."""
        self.locked = False
        self.locked_until = None
        self.failed_login_attempts = 0


class UserSession(BaseModel, AuditMixin):
    """
    User session tracking for security and analytics.
    """
    
    __tablename__ = 'user_sessions'
    
    # Relationships
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    user = relationship("User", back_populates="sessions")
    
    # Session Information
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Timing
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Session Details
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # "desktop", "mobile", "tablet"
    browser = Column(String(100), nullable=True)
    operating_system = Column(String(100), nullable=True)
    
    # Geographic Information
    country = Column(String(2), nullable=True)  # ISO country code
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Session Status
    active = Column(Boolean, nullable=False, default=True)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(100), nullable=True)
    
    # Security
    suspicious_activity = Column(Boolean, nullable=False, default=False)
    risk_score = Column(Float, nullable=False, default=0.0)  # 0-1 scale
    
    # Usage Tracking
    page_views = Column(Integer, nullable=False, default=0)
    api_calls = Column(Integer, nullable=False, default=0)
    
    # Additional Session Data
    session_data = Column(JSONB, nullable=True)
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, token={self.session_token[:8]}...)>"
    
    @property
    def is_expired(self):
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if session is valid and active."""
        return self.active and not self.revoked and not self.is_expired
    
    @property
    def duration_minutes(self):
        """Get session duration in minutes."""
        if not self.last_activity:
            return 0
        
        duration = self.last_activity - self.created_at
        return round(duration.total_seconds() / 60, 1)
    
    @property
    def idle_minutes(self):
        """Get minutes since last activity."""
        if not self.last_activity:
            return 0
        
        idle_time = datetime.utcnow() - self.last_activity
        return round(idle_time.total_seconds() / 60, 1)
    
    def extend_session(self, hours=24):
        """Extend session expiration."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.update_activity()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def revoke(self, reason="user_logout"):
        """Revoke the session."""
        self.active = False
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason
    
    def flag_suspicious(self, risk_score=0.8):
        """Flag session as suspicious."""
        self.suspicious_activity = True
        self.risk_score = max(self.risk_score, risk_score)
    
    def increment_usage(self, page_view=True, api_call=False):
        """Increment usage counters."""
        if page_view:
            self.page_views += 1
        if api_call:
            self.api_calls += 1
        
        self.update_activity()