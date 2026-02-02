from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy import Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class DealStage(str, enum.Enum):
    INQUIRY = "inquiry"           # פנייה ראשונית
    TOUR_SCHEDULED = "tour_scheduled"  # סיור תואם
    TOUR_COMPLETED = "tour_completed"  # סיור בוצע
    PROPOSAL = "proposal"         # הצעה
    NEGOTIATION = "negotiation"   # משא ומתן
    LOI_SIGNED = "loi_signed"     # כתב כוונות
    LEGAL_REVIEW = "legal_review" # בדיקה משפטית
    SIGNED = "signed"             # חוזה נחתם
    LOST = "lost"                 # עסקה אבודה
    WITHDRAWN = "withdrawn"       # בוטל


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    broker_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Deal info
    stage = Column(SQLEnum(DealStage), default=DealStage.INQUIRY, nullable=False, index=True)
    proposed_price = Column(Float, nullable=True)
    final_price = Column(Float, nullable=True)
    proposed_area_sqm = Column(Float, nullable=True)
    lease_term_months = Column(Integer, nullable=True)

    # Timeline
    inquiry_date = Column(DateTime(timezone=True), server_default=func.now())
    tour_date = Column(DateTime(timezone=True), nullable=True)
    proposal_date = Column(DateTime(timezone=True), nullable=True)
    loi_date = Column(DateTime(timezone=True), nullable=True)
    signed_date = Column(DateTime(timezone=True), nullable=True)
    lost_date = Column(DateTime(timezone=True), nullable=True)
    expected_move_in = Column(DateTime(timezone=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    lost_reason = Column(String(255), nullable=True)

    # Activity log
    activity_log = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    listing = relationship("Listing", back_populates="deals")
    tenant = relationship("User", back_populates="deals_as_tenant", foreign_keys=[tenant_id])
    broker = relationship("User", back_populates="deals_as_broker", foreign_keys=[broker_id])

    __table_args__ = (
        Index("ix_deals_stage_date", "stage", "inquiry_date"),
    )
