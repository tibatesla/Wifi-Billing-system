import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

def get_utc_now():
    return datetime.now(timezone.utc)
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    
    # Safaricom Daraja Credentials (Encrypted in production)
    daraja_shortcode: Mapped[Optional[str]] = mapped_column(String(50))
    daraja_consumer_key: Mapped[Optional[str]] = mapped_column(String(255))
    daraja_consumer_secret: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    customers: Mapped[List["Customer"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    routers: Mapped[List["Router"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    plans: Mapped[List["Plan"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """Admin and Reseller accounts."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="TENANT_ADMIN") # SUPER_ADMIN, TENANT_ADMIN, RESELLER
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")


class Router(Base):
    """MikroTik routers linked to a specific tenant."""
    __tablename__ = "routers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    api_port: Mapped[int] = mapped_column(Integer, default=8728)
    api_username: Mapped[str] = mapped_column(String(100), nullable=False)
    api_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OFFLINE")

    tenant: Mapped["Tenant"] = relationship(back_populates="routers")
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="router")


class Plan(Base):
    """Internet packages configured by the ISP."""
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    speed_limit: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "10M/10M"
    validity_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    mikrotik_profile_name: Mapped[str] = mapped_column(String(100), nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="plans")


class Customer(Base):
    """The end-user connecting to the Wi-Fi."""
    __tablename__ = "customers"
    __table_args__ = (
        # Prevent duplicate phone numbers WITHIN the same ISP, 
        # but allow two different ISPs to have the same customer.
        UniqueConstraint("tenant_id", "phone_number", name="uq_tenant_phone"),
        # Composite index for rapid captive portal lookups
        Index("ix_tenant_phone", "tenant_id", "phone_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=False)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")

    tenant: Mapped["Tenant"] = relationship(back_populates="customers")
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class Subscription(Base):
    """Active or expired internet sessions."""
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id"), index=True)
    router_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("routers.id"), index=True)
    
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE") # ACTIVE, EXPIRED, SUSPENDED

    customer: Mapped["Customer"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship()
    router: Mapped["Router"] = relationship(back_populates="subscriptions")


class Transaction(Base):
    """M-Pesa payment logs."""
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("customers.id"), index=True)
    
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    checkout_request_id: Mapped[str] = mapped_column(String(100), unique=True, index=True) # STK Push Tracker
    mpesa_receipt: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING") # PENDING, SUCCESS, FAILED
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)qqq