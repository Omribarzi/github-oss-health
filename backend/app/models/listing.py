from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy import Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ListingType(str, enum.Enum):
    LEASE = "lease"       # השכרה
    SUBLEASE = "sublease" # השכרת משנה
    SALE = "sale"         # מכירה


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    LEASED = "leased"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class PricePeriod(str, enum.Enum):
    MONTHLY = "monthly"       # חודשי
    ANNUAL = "annual"         # שנתי
    PER_SQM_MONTHLY = "per_sqm_monthly"  # למ"ר לחודש
    PER_SQM_ANNUAL = "per_sqm_annual"    # למ"ר לשנה
    TOTAL = "total"           # סה"כ (for sale)


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("property_units.id"), nullable=True, index=True)
    broker_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Listing info
    title = Column(String(255), nullable=False)
    title_he = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    description_he = Column(Text, nullable=True)
    listing_type = Column(SQLEnum(ListingType), nullable=False, default=ListingType.LEASE)
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE, index=True)

    # Pricing (ILS - Israeli New Shekel)
    price = Column(Float, nullable=False)
    price_period = Column(SQLEnum(PricePeriod), default=PricePeriod.MONTHLY)
    management_fee_monthly = Column(Float, nullable=True)  # דמי ניהול
    arnona_monthly = Column(Float, nullable=True)           # ארנונה
    negotiable = Column(Boolean, default=True)

    # Area
    available_area_sqm = Column(Float, nullable=False)
    min_area_sqm = Column(Float, nullable=True)  # Minimum divisible area

    # Lease terms
    min_lease_months = Column(Integer, nullable=True)
    max_lease_months = Column(Integer, nullable=True)
    available_from = Column(DateTime(timezone=True), nullable=True)

    # Features
    furnished = Column(Boolean, default=False)
    condition = Column(String(50), nullable=True)  # shell, fitted, furnished

    # Engagement tracking
    view_count = Column(Integer, default=0)
    inquiry_count = Column(Integer, default=0)
    tour_count = Column(Integer, default=0)

    # Dates
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="listings")
    unit = relationship("PropertyUnit", back_populates="listings")
    broker = relationship("User", back_populates="listings")
    deals = relationship("Deal", back_populates="listing")
    favorites = relationship("Favorite", back_populates="listing")
    tours = relationship("Tour", back_populates="listing")

    __table_args__ = (
        Index("ix_listings_status_type", "status", "listing_type"),
        Index("ix_listings_price", "price"),
        Index("ix_listings_area", "available_area_sqm"),
    )
