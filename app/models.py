from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


# Enums for status values
class ServiceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class ActionType(str, Enum):
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    SERVICE_RESTART = "service_restart"
    USER_CREATE = "user_create"
    USER_DELETE = "user_delete"
    PASSWORD_RESET = "password_reset"
    LOGIN = "login"
    LOGOUT = "logout"


class ActionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


# Persistent models (stored in database)
class SystemMetric(SQLModel, table=True):
    """Stores historical system metrics for dashboard graphs and analytics"""

    __tablename__ = "system_metrics"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    cpu_usage_percent: Decimal = Field(decimal_places=2, max_digits=5)  # 0-100.00
    memory_usage_percent: Decimal = Field(decimal_places=2, max_digits=5)  # 0-100.00
    memory_total_gb: Decimal = Field(decimal_places=2, max_digits=10)
    memory_used_gb: Decimal = Field(decimal_places=2, max_digits=10)
    disk_usage_percent: Decimal = Field(decimal_places=2, max_digits=5)  # 0-100.00
    disk_total_gb: Decimal = Field(decimal_places=2, max_digits=15)
    disk_used_gb: Decimal = Field(decimal_places=2, max_digits=15)
    load_average_1min: Decimal = Field(decimal_places=2, max_digits=8)
    load_average_5min: Decimal = Field(decimal_places=2, max_digits=8)
    load_average_15min: Decimal = Field(decimal_places=2, max_digits=8)


class ServerInfo(SQLModel, table=True):
    """Stores server information and configuration"""

    __tablename__ = "server_info"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    hostname: str = Field(max_length=255)
    operating_system: str = Field(max_length=100)
    kernel_version: str = Field(max_length=100)
    architecture: str = Field(max_length=50)
    boot_time: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    additional_info: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))


class SystemUser(SQLModel, table=True):
    """Represents system users that can be managed through the panel"""

    __tablename__ = "system_users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=32, regex=r"^[a-z_][a-z0-9_-]*[$]?$")
    uid: int = Field(unique=True)
    gid: int
    home_directory: str = Field(max_length=500)
    shell: str = Field(max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=200)
    is_system_user: bool = Field(default=False)
    is_locked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
    groups: List[str] = Field(default=[], sa_column=Column(JSON))

    # Relationships
    audit_logs: List["AuditLog"] = Relationship(back_populates="target_user")


class SystemService(SQLModel, table=True):
    """Represents systemd services that can be managed"""

    __tablename__ = "system_services"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    service_name: str = Field(unique=True, max_length=255, index=True)
    display_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: ServiceStatus = Field(default=ServiceStatus.UNKNOWN)
    is_enabled: bool = Field(default=False)
    is_active: bool = Field(default=False)
    main_pid: Optional[int] = Field(default=None)
    memory_usage_bytes: Optional[int] = Field(default=None)
    cpu_usage_percent: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=5)
    last_started: Optional[datetime] = Field(default=None)
    last_updated: datetime = Field(default_factory=datetime.utcnow, index=True)
    restart_count: int = Field(default=0)
    unit_file_path: Optional[str] = Field(default=None, max_length=500)

    # Service-specific configuration
    service_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))


class AdminUser(SQLModel, table=True):
    """Web panel administrator users"""

    __tablename__ = "admin_users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=50)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password_hash: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    last_login: Optional[datetime] = Field(default=None)
    failed_login_attempts: int = Field(default=0)
    account_locked_until: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Security settings
    require_password_change: bool = Field(default=False)
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
    two_factor_enabled: bool = Field(default=False)
    two_factor_secret: Optional[str] = Field(default=None, max_length=32)

    # Relationships
    sessions: List["AdminSession"] = Relationship(back_populates="admin_user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="admin_user")


class AdminSession(SQLModel, table=True):
    """Active admin user sessions for security tracking"""

    __tablename__ = "admin_sessions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(unique=True, max_length=128, index=True)
    admin_user_id: int = Field(foreign_key="admin_users.id", index=True)
    ip_address: str = Field(max_length=45)  # IPv6 compatible
    user_agent: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow, index=True)
    expires_at: datetime = Field(index=True)
    is_active: bool = Field(default=True, index=True)

    # Relationships
    admin_user: AdminUser = Relationship(back_populates="sessions")


class AuditLog(SQLModel, table=True):
    """Comprehensive audit logging for security and compliance"""

    __tablename__ = "audit_logs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    admin_user_id: Optional[int] = Field(default=None, foreign_key="admin_users.id", index=True)
    target_user_id: Optional[int] = Field(default=None, foreign_key="system_users.id", index=True)
    action_type: ActionType = Field(index=True)
    action_status: ActionStatus = Field(default=ActionStatus.SUCCESS)
    resource_name: Optional[str] = Field(default=None, max_length=255, index=True)
    ip_address: str = Field(max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    command_executed: Optional[str] = Field(default=None, max_length=2000)
    error_message: Optional[str] = Field(default=None, max_length=2000)
    execution_time_ms: Optional[int] = Field(default=None)

    # Additional context data
    context_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    admin_user: Optional[AdminUser] = Relationship(back_populates="audit_logs")
    target_user: Optional[SystemUser] = Relationship(back_populates="audit_logs")


class SystemAlert(SQLModel, table=True):
    """System alerts and notifications for monitoring"""

    __tablename__ = "system_alerts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_type: str = Field(max_length=50, index=True)  # cpu_high, disk_full, service_down, etc.
    severity: str = Field(max_length=20, index=True)  # critical, warning, info
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    resource_name: Optional[str] = Field(default=None, max_length=255)
    threshold_value: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    current_value: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    resolved_at: Optional[datetime] = Field(default=None, index=True)
    is_acknowledged: bool = Field(default=False, index=True)
    acknowledged_by: Optional[str] = Field(default=None, max_length=50)
    acknowledged_at: Optional[datetime] = Field(default=None)

    # Alert metadata
    alert_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))


# Non-persistent schemas (for validation, forms, API requests/responses)
class SystemMetricCreate(SQLModel, table=False):
    cpu_usage_percent: Decimal = Field(ge=0.0, le=100.0)
    memory_usage_percent: Decimal = Field(ge=0.0, le=100.0)
    memory_total_gb: Decimal = Field(ge=0.0)
    memory_used_gb: Decimal = Field(ge=0.0)
    disk_usage_percent: Decimal = Field(ge=0.0, le=100.0)
    disk_total_gb: Decimal = Field(ge=0.0)
    disk_used_gb: Decimal = Field(ge=0.0)
    load_average_1min: Decimal = Field(ge=0.0)
    load_average_5min: Decimal = Field(ge=0.0)
    load_average_15min: Decimal = Field(ge=0.0)


class SystemUserCreate(SQLModel, table=False):
    username: str = Field(max_length=32, regex=r"^[a-z_][a-z0-9_-]*[$]?$")
    full_name: Optional[str] = Field(default=None, max_length=200)
    shell: str = Field(default="/bin/bash", max_length=100)
    home_directory: Optional[str] = Field(default=None, max_length=500)
    groups: List[str] = Field(default=[])
    create_home: bool = Field(default=True)
    password: Optional[str] = Field(default=None, max_length=128)


class SystemUserUpdate(SQLModel, table=False):
    full_name: Optional[str] = Field(default=None, max_length=200)
    shell: Optional[str] = Field(default=None, max_length=100)
    groups: Optional[List[str]] = Field(default=None)
    is_locked: Optional[bool] = Field(default=None)


class PasswordResetRequest(SQLModel, table=False):
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class ServiceActionRequest(SQLModel, table=False):
    action: str = Field(regex=r"^(start|stop|restart|enable|disable)$")
    service_name: str = Field(max_length=255)


class AdminUserCreate(SQLModel, table=False):
    username: str = Field(max_length=50, regex=r"^[a-zA-Z0-9_-]+$")
    email: str = Field(max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(min_length=8, max_length=128)
    is_superuser: bool = Field(default=False)


class AdminUserLogin(SQLModel, table=False):
    username: str = Field(max_length=50)
    password: str = Field(max_length=128)
    remember_me: bool = Field(default=False)


class SystemStatusResponse(SQLModel, table=False):
    """Response model for current system status"""

    cpu_usage_percent: Decimal
    memory_usage_percent: Decimal
    memory_total_gb: Decimal
    memory_used_gb: Decimal
    disk_usage_percent: Decimal
    disk_total_gb: Decimal
    disk_used_gb: Decimal
    load_average_1min: Decimal
    load_average_5min: Decimal
    load_average_15min: Decimal
    uptime_seconds: int
    hostname: str
    operating_system: str
    kernel_version: str
    timestamp: datetime


class ServiceStatusResponse(SQLModel, table=False):
    """Response model for service status"""

    service_name: str
    display_name: Optional[str]
    description: Optional[str]
    status: ServiceStatus
    is_enabled: bool
    is_active: bool
    main_pid: Optional[int]
    memory_usage_bytes: Optional[int]
    cpu_usage_percent: Optional[Decimal]
    last_started: Optional[datetime]
    restart_count: int


class DashboardMetrics(SQLModel, table=False):
    """Dashboard overview metrics"""

    current_metrics: SystemStatusResponse
    active_services_count: int
    inactive_services_count: int
    failed_services_count: int
    total_users_count: int
    active_alerts_count: int
    recent_audit_logs: List[Dict[str, Any]]
    cpu_history: List[Dict[str, Any]]  # Last 24h CPU usage points
    memory_history: List[Dict[str, Any]]  # Last 24h memory usage points


class AuditLogCreate(SQLModel, table=False):
    action_type: ActionType
    action_status: ActionStatus = Field(default=ActionStatus.SUCCESS)
    resource_name: Optional[str] = Field(default=None)
    ip_address: str
    user_agent: Optional[str] = Field(default=None)
    command_executed: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    execution_time_ms: Optional[int] = Field(default=None)
    context_data: Dict[str, Any] = Field(default={})


class AlertCreate(SQLModel, table=False):
    alert_type: str = Field(max_length=50)
    severity: str = Field(max_length=20)
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    resource_name: Optional[str] = Field(default=None)
    threshold_value: Optional[Decimal] = Field(default=None)
    current_value: Optional[Decimal] = Field(default=None)
    alert_data: Dict[str, Any] = Field(default={})
