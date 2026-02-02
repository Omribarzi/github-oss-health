from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from app.database import get_db
from app.models.property import Property, City, PropertyType, CITY_NAMES_HE, PROPERTY_TYPE_NAMES_HE
from app.models.listing import Listing, ListingStatus
from app.models.deal import Deal, DealStage
from app.models.market_stats import MarketSnapshot

router = APIRouter()


@router.get("/overview")
def market_overview(db: Session = Depends(get_db)):
    """Dashboard overview with key market metrics."""
    total_properties = db.query(func.count(Property.id)).scalar()
    total_active_listings = db.query(func.count(Listing.id)).filter(Listing.status == ListingStatus.ACTIVE).scalar()
    total_area = db.query(func.sum(Listing.available_area_sqm)).filter(Listing.status == ListingStatus.ACTIVE).scalar() or 0
    avg_price = db.query(func.avg(Listing.price)).filter(Listing.status == ListingStatus.ACTIVE).scalar()

    # Active deals (not lost/withdrawn/signed)
    active_deal_stages = [DealStage.INQUIRY, DealStage.TOUR_SCHEDULED, DealStage.TOUR_COMPLETED,
                          DealStage.PROPOSAL, DealStage.NEGOTIATION, DealStage.LOI_SIGNED, DealStage.LEGAL_REVIEW]
    active_deals = db.query(func.count(Deal.id)).filter(Deal.stage.in_(active_deal_stages)).scalar()
    signed_deals = db.query(func.count(Deal.id)).filter(Deal.stage == DealStage.SIGNED).scalar()

    return {
        "total_properties": total_properties,
        "total_active_listings": total_active_listings,
        "total_available_sqm": round(total_area, 1),
        "avg_price_ils": round(avg_price, 0) if avg_price else 0,
        "active_deals": active_deals,
        "signed_deals": signed_deals,
        "currency": "ILS",
    }


@router.get("/by-city")
def analytics_by_city(db: Session = Depends(get_db)):
    """Listing and pricing analytics broken down by city."""
    results = (
        db.query(
            Property.city,
            func.count(Listing.id).label("listing_count"),
            func.avg(Listing.price).label("avg_price"),
            func.sum(Listing.available_area_sqm).label("total_area"),
        )
        .join(Listing, Listing.property_id == Property.id)
        .filter(Listing.status == ListingStatus.ACTIVE)
        .group_by(Property.city)
        .all()
    )

    return {
        "cities": [
            {
                "city": r.city.value,
                "city_he": CITY_NAMES_HE.get(r.city, ""),
                "listing_count": r.listing_count,
                "avg_price": round(r.avg_price, 0) if r.avg_price else 0,
                "total_area_sqm": round(r.total_area, 1) if r.total_area else 0,
            }
            for r in results
        ]
    }


@router.get("/by-type")
def analytics_by_type(db: Session = Depends(get_db)):
    """Listing and pricing analytics broken down by property type."""
    results = (
        db.query(
            Property.property_type,
            func.count(Listing.id).label("listing_count"),
            func.avg(Listing.price).label("avg_price"),
            func.sum(Listing.available_area_sqm).label("total_area"),
        )
        .join(Listing, Listing.property_id == Property.id)
        .filter(Listing.status == ListingStatus.ACTIVE)
        .group_by(Property.property_type)
        .all()
    )

    return {
        "types": [
            {
                "type": r.property_type.value,
                "type_he": PROPERTY_TYPE_NAMES_HE.get(r.property_type, ""),
                "listing_count": r.listing_count,
                "avg_price": round(r.avg_price, 0) if r.avg_price else 0,
                "total_area_sqm": round(r.total_area, 1) if r.total_area else 0,
            }
            for r in results
        ]
    }


@router.get("/deal-pipeline")
def deal_pipeline_analytics(db: Session = Depends(get_db)):
    """Overall deal pipeline analytics."""
    results = db.query(Deal.stage, func.count(Deal.id)).group_by(Deal.stage).all()
    pipeline = {stage.value: 0 for stage in DealStage}
    for stage, count in results:
        pipeline[stage.value] = count

    total_value = db.query(func.sum(Deal.proposed_price)).filter(
        Deal.stage.notin_([DealStage.LOST, DealStage.WITHDRAWN])
    ).scalar() or 0

    signed_value = db.query(func.sum(Deal.final_price)).filter(
        Deal.stage == DealStage.SIGNED
    ).scalar() or 0

    return {
        "pipeline": pipeline,
        "total_pipeline_value_ils": round(total_value, 0),
        "signed_value_ils": round(signed_value, 0),
    }


@router.get("/price-trends")
def price_trends(
    city: Optional[City] = None,
    property_type: Optional[PropertyType] = None,
    db: Session = Depends(get_db),
):
    """Historical price trends from market snapshots."""
    query = db.query(MarketSnapshot).order_by(MarketSnapshot.snapshot_date.desc())

    if city:
        query = query.filter(MarketSnapshot.city == city)
    if property_type:
        query = query.filter(MarketSnapshot.property_type == property_type)

    snapshots = query.limit(100).all()

    return {
        "trends": [
            {
                "date": s.snapshot_date.isoformat() if s.snapshot_date else None,
                "city": s.city.value,
                "city_he": CITY_NAMES_HE.get(s.city, ""),
                "property_type": s.property_type.value,
                "avg_price_per_sqm": s.avg_price_per_sqm,
                "median_price_per_sqm": s.median_price_per_sqm,
                "total_listings": s.total_listings,
                "occupancy_rate": s.occupancy_rate,
                "avg_days_on_market": s.avg_days_on_market,
            }
            for s in snapshots
        ]
    }
