from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class TourStatus(str, enum.Enum):
    REQUESTED = "requested"     # נבקש
    CONFIRMED = "confirmed"     # מאושר
    COMPLETED = "completed"     # בוצע
    CANCELLED = "cancelled"     # בוטל
    NO_SHOW = "no_show"         # לא הגיע


class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(SQLEnum(TourStatus), default=TourStatus.REQUESTED)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, default=30)

    # Feedback
    notes = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    listing = relationship("Listing", back_populates="tours")
    contact = relationship("User", back_populates="tours")
