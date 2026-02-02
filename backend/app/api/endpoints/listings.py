from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.property import Property, City, PropertyType, CITY_NAMES_HE, PROPERTY_TYPE_NAMES_HE
from app.models.listing import Listing, ListingType, ListingStatus, PricePeriod
from app.utils.auth import require_user, get_current_user

router = APIRouter()


class ListingCreate(BaseModel):
    property_id: int
    unit_id: Optional[int] = None
    title: str
    title_he: Optional[str] = None
    description: Optional[str] = None
    description_he: Optional[str] = None
    listing_type: ListingType = ListingType.LEASE
    price: float
    price_period: PricePeriod = PricePeriod.MONTHLY
    management_fee_monthly: Optional[float] = None
    arnona_monthly: Optional[float] = None
    negotiable: bool = True
    available_area_sqm: float
    min_area_sqm: Optional[float] = None
    min_lease_months: Optional[int] = None
    max_lease_months: Optional[int] = None
    available_from: Optional[str] = None
    furnished: bool = False
    condition: Optional[str] = None


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    title_he: Optional[str] = None
    description: Optional[str] = None
    description_he: Optional[str] = None
    status: Optional[ListingStatus] = None
    price: Optional[float] = None
    price_period: Optional[PricePeriod] = None
    management_fee_monthly: Optional[float] = None
    arnona_monthly: Optional[float] = None
    negotiable: Optional[bool] = None
    available_area_sqm: Optional[float] = None
    min_area_sqm: Optional[float] = None
    furnished: Optional[bool] = None
    condition: Optional[str] = None


def listing_to_dict(l: Listing) -> dict:
    prop = l.property
    return {
        "id": l.id,
        "property_id": l.property_id,
        "unit_id": l.unit_id,
        "broker_id": l.broker_id,
        "title": l.title,
        "title_he": l.title_he,
        "description": l.description,
        "description_he": l.description_he,
        "listing_type": l.listing_type.value,
        "status": l.status.value if l.status else "active",
        "price": l.price,
        "price_period": l.price_period.value if l.price_period else "monthly",
        "management_fee_monthly": l.management_fee_monthly,
        "arnona_monthly": l.arnona_monthly,
        "negotiable": l.negotiable,
        "available_area_sqm": l.available_area_sqm,
        "min_area_sqm": l.min_area_sqm,
        "min_lease_months": l.min_lease_months,
        "max_lease_months": l.max_lease_months,
        "available_from": l.available_from.isoformat() if l.available_from else None,
        "furnished": l.furnished,
        "condition": l.condition,
        "view_count": l.view_count,
        "inquiry_count": l.inquiry_count,
        "tour_count": l.tour_count,
        "published_at": l.published_at.isoformat() if l.published_at else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
        "property": {
            "id": prop.id,
            "name": prop.name,
            "name_he": prop.name_he,
            "property_type": prop.property_type.value,
            "property_type_he": PROPERTY_TYPE_NAMES_HE.get(prop.property_type, ""),
            "city": prop.city.value,
            "city_he": CITY_NAMES_HE.get(prop.city, ""),
            "neighborhood": prop.neighborhood,
            "neighborhood_he": prop.neighborhood_he,
            "street_address": prop.street_address,
            "street_address_he": prop.street_address_he,
            "total_area_sqm": prop.total_area_sqm,
            "building_class": prop.building_class,
            "has_elevator": prop.has_elevator,
            "has_parking": (prop.parking_spots or 0) > 0,
            "parking_spots": prop.parking_spots,
            "images": prop.images or [],
        } if prop else None,
    }


@router.get("")
def list_listings(
    city: Optional[City] = None,
    property_type: Optional[PropertyType] = None,
    listing_type: Optional[ListingType] = None,
    status: Optional[ListingStatus] = Query(default=None),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    furnished: Optional[bool] = None,
    sort_by: str = Query(default="created_at", regex="^(created_at|price|available_area_sqm|view_count)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Listing).join(Property).options(joinedload(Listing.property))

    # Default to active listings
    if status:
        query = query.filter(Listing.status == status)
    else:
        query = query.filter(Listing.status == ListingStatus.ACTIVE)

    if city:
        query = query.filter(Property.city == city)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if listing_type:
        query = query.filter(Listing.listing_type == listing_type)
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    if min_area is not None:
        query = query.filter(Listing.available_area_sqm >= min_area)
    if max_area is not None:
        query = query.filter(Listing.available_area_sqm <= max_area)
    if furnished is not None:
        query = query.filter(Listing.furnished == furnished)

    total = query.count()

    sort_col = getattr(Listing, sort_by)
    if sort_order == "desc":
        sort_col = sort_col.desc()
    query = query.order_by(sort_col)
    listings = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "listings": [listing_to_dict(l) for l in listings],
    }


@router.get("/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).options(joinedload(Listing.property)).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Increment view count
    listing.view_count = (listing.view_count or 0) + 1
    db.commit()

    return listing_to_dict(listing)


@router.post("")
def create_listing(req: ListingCreate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == req.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.owner_id != user.id and user.role.value not in ("admin", "broker"):
        raise HTTPException(status_code=403, detail="Not authorized to create listings for this property")

    listing = Listing(
        property_id=req.property_id,
        unit_id=req.unit_id,
        broker_id=user.id if user.role.value == "broker" else None,
        title=req.title,
        title_he=req.title_he,
        description=req.description,
        description_he=req.description_he,
        listing_type=req.listing_type,
        price=req.price,
        price_period=req.price_period,
        management_fee_monthly=req.management_fee_monthly,
        arnona_monthly=req.arnona_monthly,
        negotiable=req.negotiable,
        available_area_sqm=req.available_area_sqm,
        min_area_sqm=req.min_area_sqm,
        min_lease_months=req.min_lease_months,
        max_lease_months=req.max_lease_months,
        furnished=req.furnished,
        condition=req.condition,
        published_at=datetime.now(timezone.utc),
        status=ListingStatus.ACTIVE,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing_to_dict(listing)


@router.put("/{listing_id}")
def update_listing(listing_id: int, req: ListingUpdate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    listing = db.query(Listing).options(joinedload(Listing.property)).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.property.owner_id != user.id and user.role.value != "admin" and listing.broker_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return listing_to_dict(listing)
