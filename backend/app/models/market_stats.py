from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy import Enum as SQLEnum, Index
from sqlalchemy.sql import func
from app.database import Base
from app.models.property import City, PropertyType


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())
    city = Column(SQLEnum(City), nullable=False)
    property_type = Column(SQLEnum(PropertyType), nullable=False)

    # Pricing analytics (ILS per sqm per month)
    avg_price_per_sqm = Column(Float, nullable=True)
    median_price_per_sqm = Column(Float, nullable=True)
    min_price_per_sqm = Column(Float, nullable=True)
    max_price_per_sqm = Column(Float, nullable=True)

    # Inventory
    total_listings = Column(Integer, default=0)
    total_available_sqm = Column(Float, default=0)
    new_listings_count = Column(Integer, default=0)
    absorbed_listings_count = Column(Integer, default=0)

    # Velocity
    avg_days_on_market = Column(Float, nullable=True)
    occupancy_rate = Column(Float, nullable=True)  # 0-100

    # Deal activity
    deals_closed = Column(Integer, default=0)
    avg_deal_price_per_sqm = Column(Float, nullable=True)
    avg_lease_term_months = Column(Float, nullable=True)

    # Raw data
    details_json = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_market_city_type_date", "city", "property_type", "snapshot_date"),
    )
