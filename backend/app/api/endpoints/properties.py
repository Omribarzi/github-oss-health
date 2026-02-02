from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.property import Property, PropertyUnit, PropertyType, PropertyStatus, City, CITY_NAMES_HE, PROPERTY_TYPE_NAMES_HE
from app.utils.auth import require_user, get_current_user

router = APIRouter()


class PropertyUnitCreate(BaseModel):
    unit_number: str
    floor: Optional[int] = None
    area_sqm: float
    unit_type: Optional[PropertyType] = None
    rooms: Optional[int] = None
    has_balcony: bool = False
    has_kitchenette: bool = False
    has_server_room: bool = False
    ceiling_height_m: Optional[float] = None


class PropertyCreate(BaseModel):
    name: str
    name_he: Optional[str] = None
    description: Optional[str] = None
    description_he: Optional[str] = None
    property_type: PropertyType
    city: City
    neighborhood: Optional[str] = None
    neighborhood_he: Optional[str] = None
    street_address: Optional[str] = None
    street_address_he: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_area_sqm: float
    floor_count: Optional[int] = None
    year_built: Optional[int] = None
    parking_spots: int = 0
    has_elevator: bool = False
    has_loading_dock: bool = False
    has_generator: bool = False
    accessibility: bool = False
    building_class: Optional[str] = None
    energy_rating: Optional[str] = None
    arnona_zone: Optional[str] = None
    images: List[str] = []
    floor_plans: List[str] = []
    virtual_tour_url: Optional[str] = None
    units: List[PropertyUnitCreate] = []


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    name_he: Optional[str] = None
    description: Optional[str] = None
    description_he: Optional[str] = None
    status: Optional[PropertyStatus] = None
    parking_spots: Optional[int] = None
    has_elevator: Optional[bool] = None
    has_loading_dock: Optional[bool] = None
    has_generator: Optional[bool] = None
    accessibility: Optional[bool] = None
    building_class: Optional[str] = None
    images: Optional[List[str]] = None
    floor_plans: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None


def property_to_dict(p: Property) -> dict:
    return {
        "id": p.id,
        "owner_id": p.owner_id,
        "name": p.name,
        "name_he": p.name_he,
        "description": p.description,
        "description_he": p.description_he,
        "property_type": p.property_type.value,
        "property_type_he": PROPERTY_TYPE_NAMES_HE.get(p.property_type, ""),
        "status": p.status.value if p.status else "active",
        "city": p.city.value,
        "city_he": CITY_NAMES_HE.get(p.city, ""),
        "neighborhood": p.neighborhood,
        "neighborhood_he": p.neighborhood_he,
        "street_address": p.street_address,
        "street_address_he": p.street_address_he,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "total_area_sqm": p.total_area_sqm,
        "floor_count": p.floor_count,
        "year_built": p.year_built,
        "parking_spots": p.parking_spots,
        "has_elevator": p.has_elevator,
        "has_loading_dock": p.has_loading_dock,
        "has_generator": p.has_generator,
        "accessibility": p.accessibility,
        "building_class": p.building_class,
        "energy_rating": p.energy_rating,
        "arnona_zone": p.arnona_zone,
        "images": p.images or [],
        "floor_plans": p.floor_plans or [],
        "virtual_tour_url": p.virtual_tour_url,
        "units": [
            {
                "id": u.id,
                "unit_number": u.unit_number,
                "floor": u.floor,
                "area_sqm": u.area_sqm,
                "is_available": u.is_available,
                "unit_type": u.unit_type.value if u.unit_type else None,
                "rooms": u.rooms,
                "has_balcony": u.has_balcony,
                "has_kitchenette": u.has_kitchenette,
                "has_server_room": u.has_server_room,
                "ceiling_height_m": u.ceiling_height_m,
            }
            for u in (p.units or [])
        ],
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("")
def list_properties(
    city: Optional[City] = None,
    property_type: Optional[PropertyType] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    building_class: Optional[str] = None,
    has_elevator: Optional[bool] = None,
    has_parking: Optional[bool] = None,
    sort_by: str = Query(default="created_at", regex="^(created_at|total_area_sqm|name)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Property).options(joinedload(Property.units))

    if city:
        query = query.filter(Property.city == city)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if min_area:
        query = query.filter(Property.total_area_sqm >= min_area)
    if max_area:
        query = query.filter(Property.total_area_sqm <= max_area)
    if building_class:
        query = query.filter(Property.building_class == building_class)
    if has_elevator is not None:
        query = query.filter(Property.has_elevator == has_elevator)
    if has_parking:
        query = query.filter(Property.parking_spots > 0)

    total = query.count()
    sort_col = getattr(Property, sort_by)
    if sort_order == "desc":
        sort_col = sort_col.desc()
    query = query.order_by(sort_col)
    properties = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "properties": [property_to_dict(p) for p in properties],
    }


@router.get("/cities")
def list_cities():
    return {"cities": [{"value": c.value, "label_he": CITY_NAMES_HE[c]} for c in City]}


@router.get("/types")
def list_property_types():
    return {"types": [{"value": t.value, "label_he": PROPERTY_TYPE_NAMES_HE[t]} for t in PropertyType]}


@router.get("/{property_id}")
def get_property(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).options(joinedload(Property.units)).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_to_dict(p)


@router.post("")
def create_property(req: PropertyCreate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if user.role.value not in ("landlord", "admin", "broker"):
        raise HTTPException(status_code=403, detail="Only landlords, brokers, or admins can create properties")

    prop = Property(
        owner_id=user.id,
        name=req.name,
        name_he=req.name_he,
        description=req.description,
        description_he=req.description_he,
        property_type=req.property_type,
        city=req.city,
        neighborhood=req.neighborhood,
        neighborhood_he=req.neighborhood_he,
        street_address=req.street_address,
        street_address_he=req.street_address_he,
        latitude=req.latitude,
        longitude=req.longitude,
        total_area_sqm=req.total_area_sqm,
        floor_count=req.floor_count,
        year_built=req.year_built,
        parking_spots=req.parking_spots,
        has_elevator=req.has_elevator,
        has_loading_dock=req.has_loading_dock,
        has_generator=req.has_generator,
        accessibility=req.accessibility,
        building_class=req.building_class,
        energy_rating=req.energy_rating,
        arnona_zone=req.arnona_zone,
        images=req.images,
        floor_plans=req.floor_plans,
        virtual_tour_url=req.virtual_tour_url,
    )
    db.add(prop)
    db.flush()

    for u in req.units:
        unit = PropertyUnit(
            property_id=prop.id,
            unit_number=u.unit_number,
            floor=u.floor,
            area_sqm=u.area_sqm,
            unit_type=u.unit_type,
            rooms=u.rooms,
            has_balcony=u.has_balcony,
            has_kitchenette=u.has_kitchenette,
            has_server_room=u.has_server_room,
            ceiling_height_m=u.ceiling_height_m,
        )
        db.add(unit)

    db.commit()
    db.refresh(prop)
    return property_to_dict(prop)


@router.put("/{property_id}")
def update_property(property_id: int, req: PropertyUpdate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)

    db.commit()
    db.refresh(prop)
    return property_to_dict(prop)
