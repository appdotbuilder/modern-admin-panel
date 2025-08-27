from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


# Enums for type safety
class ServiceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ServiceAction(str, Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    RELOAD = "reload"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    START_SERVICE = "start_service"
    STOP_SERVICE = "stop_service"
    RESTART_SERVICE = "restart_service"


# Persistent models (stored in database)
class SystemUser(SQLModel, table=True):
    """System users for user management"""

    __tablename__ = "system_users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    full_name: str = Field(max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    uid: Optional[int] = Field(default=None, unique=True)  # System UID
    gid: Optional[int] = Field(default=None)  # Primary group ID
    home_directory: Optional[str] = Field(default=None, max_length=500)
    shell: Optional[str] = Field(default="/bin/bash", max_length=100)
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")


class SystemService(SQLModel, table=True):
    """System services for service management"""

    __tablename__ = "system_services"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    display_name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: ServiceStatus = Field(default=ServiceStatus.UNKNOWN)
    enabled: bool = Field(default=False)  # Whether service is enabled to start at boot
    pid: Optional[int] = Field(default=None)  # Process ID when running
    memory_usage: Optional[Decimal] = Field(default=Decimal("0"), decimal_places=2)  # MB
    cpu_usage: Optional[Decimal] = Field(default=Decimal("0"), decimal_places=2)  # Percentage
    uptime_seconds: Optional[int] = Field(default=None)
    last_status_check: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    audit_logs: List["AuditLog"] = Relationship(back_populates="service")


class SystemMetrics(SQLModel, table=True):
    """System performance metrics for dashboard"""

    __tablename__ = "system_metrics"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    cpu_usage_percent: Decimal = Field(decimal_places=2)
    memory_total_mb: Decimal = Field(decimal_places=2)
    memory_used_mb: Decimal = Field(decimal_places=2)
    memory_usage_percent: Decimal = Field(decimal_places=2)
    disk_total_gb: Decimal = Field(decimal_places=2)
    disk_used_gb: Decimal = Field(decimal_places=2)
    disk_usage_percent: Decimal = Field(decimal_places=2)
    load_average_1m: Optional[Decimal] = Field(default=None, decimal_places=2)
    load_average_5m: Optional[Decimal] = Field(default=None, decimal_places=2)
    load_average_15m: Optional[Decimal] = Field(default=None, decimal_places=2)
    network_bytes_sent: Optional[int] = Field(default=None)
    network_bytes_recv: Optional[int] = Field(default=None)


class AuditLog(SQLModel, table=True):
    """Audit trail for all admin panel actions"""

    __tablename__ = "audit_logs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="system_users.id")
    action: AuditAction
    resource_type: str = Field(max_length=50)  # user, service, system, etc.
    resource_id: Optional[str] = Field(default=None, max_length=100)
    resource_name: Optional[str] = Field(default=None, max_length=200)
    details: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 compatible
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Foreign key relationships
    user: Optional[SystemUser] = Relationship(back_populates="audit_logs")
    service_id: Optional[int] = Field(default=None, foreign_key="system_services.id")
    service: Optional[SystemService] = Relationship(back_populates="audit_logs")


class SystemConfiguration(SQLModel, table=True):
    """Configuration settings for the admin panel"""

    __tablename__ = "system_configurations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(max_length=100, unique=True, index=True)
    value: str = Field(max_length=2000)
    description: Optional[str] = Field(default=None, max_length=500)
    category: str = Field(max_length=50, default="general")
    is_encrypted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class SystemUserCreate(SQLModel, table=False):
    username: str = Field(max_length=50)
    full_name: str = Field(max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    home_directory: Optional[str] = Field(default=None, max_length=500)
    shell: Optional[str] = Field(default="/bin/bash", max_length=100)


class SystemUserUpdate(SQLModel, table=False):
    full_name: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    role: Optional[UserRole] = Field(default=None)
    home_directory: Optional[str] = Field(default=None, max_length=500)
    shell: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = Field(default=None)


class ServiceActionRequest(SQLModel, table=False):
    service_name: str = Field(max_length=100)
    action: ServiceAction
    force: bool = Field(default=False)


class SystemMetricsResponse(SQLModel, table=False):
    timestamp: str  # ISO format timestamp
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    memory_total_mb: float
    memory_used_mb: float
    disk_total_gb: float
    disk_used_gb: float
    load_average_1m: Optional[float] = None
    load_average_5m: Optional[float] = None
    load_average_15m: Optional[float] = None


class DashboardData(SQLModel, table=False):
    current_metrics: SystemMetricsResponse
    active_services_count: int
    inactive_services_count: int
    total_users_count: int
    recent_activities: List[Dict[str, Any]]
    system_uptime_seconds: Optional[int] = None


class ServiceStatusUpdate(SQLModel, table=False):
    name: str
    status: ServiceStatus
    pid: Optional[int] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    uptime_seconds: Optional[int] = None


class AuditLogCreate(SQLModel, table=False):
    user_id: Optional[int] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    details: Dict[str, Any] = Field(default={})
    ip_address: Optional[str] = None
    success: bool = Field(default=True)
    error_message: Optional[str] = None


class ConfigurationUpdate(SQLModel, table=False):
    key: str
    value: str
    description: Optional[str] = None
    category: str = Field(default="general")
