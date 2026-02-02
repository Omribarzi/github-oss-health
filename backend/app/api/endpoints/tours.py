from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.listing import Listing
from app.models.tour import Tour, TourStatus
from app.utils.auth import require_user

router = APIRouter()


class TourCreate(BaseModel):
    listing_id: int
    scheduled_at: str
    duration_minutes: int = 30
    notes: Optional[str] = None


class TourUpdate(BaseModel):
    status: Optional[TourStatus] = None
    scheduled_at: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = None


def tour_to_dict(t: Tour) -> dict:
    return {
        "id": t.id,
        "listing_id": t.listing_id,
        "contact_id": t.contact_id,
        "status": t.status.value if t.status else "requested",
        "scheduled_at": t.scheduled_at.isoformat() if t.scheduled_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "duration_minutes": t.duration_minutes,
        "notes": t.notes,
        "rating": t.rating,
        "listing": {
            "id": t.listing.id,
            "title": t.listing.title,
            "title_he": t.listing.title_he,
        } if t.listing else None,
        "contact": {
            "id": t.contact.id,
            "full_name": t.contact.full_name,
            "phone": t.contact.phone,
        } if t.contact else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("")
def list_tours(
    status: Optional[TourStatus] = None,
    listing_id: Optional[int] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = db.query(Tour).options(joinedload(Tour.listing), joinedload(Tour.contact))

    if user.role.value == "tenant":
        query = query.filter(Tour.contact_id == user.id)
    elif user.role.value in ("landlord", "broker"):
        query = query.join(Listing).filter(
            (Listing.broker_id == user.id) | (Listing.property.has(owner_id=user.id))
        )

    if status:
        query = query.filter(Tour.status == status)
    if listing_id:
        query = query.filter(Tour.listing_id == listing_id)

    total = query.count()
    tours = query.order_by(Tour.scheduled_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "tours": [tour_to_dict(t) for t in tours],
    }


@router.post("")
def create_tour(req: TourCreate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing.tour_count = (listing.tour_count or 0) + 1

    tour = Tour(
        listing_id=req.listing_id,
        contact_id=user.id,
        scheduled_at=datetime.fromisoformat(req.scheduled_at),
        duration_minutes=req.duration_minutes,
        notes=req.notes,
        status=TourStatus.REQUESTED,
    )
    db.add(tour)
    db.commit()
    db.refresh(tour)
    return tour_to_dict(tour)


@router.put("/{tour_id}")
def update_tour(tour_id: int, req: TourUpdate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    tour = db.query(Tour).options(joinedload(Tour.listing), joinedload(Tour.contact)).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    if req.status:
        tour.status = req.status
        if req.status == TourStatus.COMPLETED:
            tour.completed_at = datetime.now(timezone.utc)
    if req.scheduled_at:
        tour.scheduled_at = datetime.fromisoformat(req.scheduled_at)
    if req.notes is not None:
        tour.notes = req.notes
    if req.rating is not None:
        tour.rating = req.rating

    db.commit()
    db.refresh(tour)
    return tour_to_dict(tour)
