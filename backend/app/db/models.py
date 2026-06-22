import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, Index, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

def get_utc_now():
    return datetime.now(timezone.utc)

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    daraja_shortcode: Mapped[Optional[str]] = mapped_column(String(50))
    daraja_consumer_key: Mapped[Optional[str]] = mapped_column(String(255))
    daraja_consumer_secret: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    users: Mapped[List["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    customers: Mapped[List["Customer"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    routers: Mapped[List["Router"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    plans: Mapped[List["Plan"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="TENANT_ADMIN") 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")

class Router(Base):
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
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    speed_limit: Mapped[str] = mapped_column(String(50), nullable=False) 
    validity_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    mikrotik_profile_name: Mapped[str] = mapped_column(String(100), nullable=False, default="default")

    tenant: Mapped["Tenant"] = relationship(back_populates="plans")

class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "phone_number", name="uq_tenant_phone"),
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
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id"), index=True)
    router_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("routers.id"), index=True)
    
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE") 

    customer: Mapped["Customer"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship()
    router: Mapped["Router"] = relationship(back_populates="subscriptions")

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("customers.id"), index=True)
    
    #  Link the transaction to the plan being purchased
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("plans.id"), index=True)
    
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    checkout_request_id: Mapped[str] = mapped_column(String(100), unique=True, index=True) 
    mpesa_receipt: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING") 
    
    #  Zero-Cost Device Transfer Columns 
    transfer_pin: Mapped[Optional[str]] = mapped_column(String(6), unique=True, index=True)
    authorized_mac: Mapped[Optional[str]] = mapped_column(String(17)) 
    is_transferred: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    # Relationships mapped for ease of querying later
    tenant: Mapped["Tenant"] = relationship()
    customer: Mapped[Optional["Customer"]] = relationship()
    plan: Mapped[Optional["Plan"]] = relationship()