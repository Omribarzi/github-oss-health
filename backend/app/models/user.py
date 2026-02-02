from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    LANDLORD = "landlord"
    TENANT = "tenant"
    BROKER = "broker"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    full_name_he = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.TENANT)
    company = Column(String(255), nullable=True)
    company_he = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    properties = relationship("Property", back_populates="owner")
    listings = relationship("Listing", back_populates="broker", foreign_keys="Listing.broker_id")
    deals_as_tenant = relationship("Deal", back_populates="tenant", foreign_keys="Deal.tenant_id")
    deals_as_broker = relationship("Deal", back_populates="broker", foreign_keys="Deal.broker_id")
    favorites = relationship("Favorite", back_populates="user")
    tours = relationship("Tour", back_populates="contact")
