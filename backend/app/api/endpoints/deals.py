from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.listing import Listing
from app.models.deal import Deal, DealStage
from app.utils.auth import require_user

router = APIRouter()


class DealCreate(BaseModel):
    listing_id: int
    proposed_price: Optional[float] = None
    proposed_area_sqm: Optional[float] = None
    lease_term_months: Optional[int] = None
    notes: Optional[str] = None


class DealUpdate(BaseModel):
    stage: Optional[DealStage] = None
    proposed_price: Optional[float] = None
    final_price: Optional[float] = None
    lease_term_months: Optional[int] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None
    expected_move_in: Optional[str] = None


STAGE_ORDER = [
    DealStage.INQUIRY,
    DealStage.TOUR_SCHEDULED,
    DealStage.TOUR_COMPLETED,
    DealStage.PROPOSAL,
    DealStage.NEGOTIATION,
    DealStage.LOI_SIGNED,
    DealStage.LEGAL_REVIEW,
    DealStage.SIGNED,
]


def deal_to_dict(d: Deal) -> dict:
    return {
        "id": d.id,
        "listing_id": d.listing_id,
        "tenant_id": d.tenant_id,
        "broker_id": d.broker_id,
        "stage": d.stage.value,
        "proposed_price": d.proposed_price,
        "final_price": d.final_price,
        "proposed_area_sqm": d.proposed_area_sqm,
        "lease_term_months": d.lease_term_months,
        "inquiry_date": d.inquiry_date.isoformat() if d.inquiry_date else None,
        "tour_date": d.tour_date.isoformat() if d.tour_date else None,
        "proposal_date": d.proposal_date.isoformat() if d.proposal_date else None,
        "loi_date": d.loi_date.isoformat() if d.loi_date else None,
        "signed_date": d.signed_date.isoformat() if d.signed_date else None,
        "lost_date": d.lost_date.isoformat() if d.lost_date else None,
        "expected_move_in": d.expected_move_in.isoformat() if d.expected_move_in else None,
        "notes": d.notes,
        "lost_reason": d.lost_reason,
        "activity_log": d.activity_log or [],
        "listing": {
            "id": d.listing.id,
            "title": d.listing.title,
            "title_he": d.listing.title_he,
            "price": d.listing.price,
        } if d.listing else None,
        "tenant": {
            "id": d.tenant.id,
            "full_name": d.tenant.full_name,
            "company": d.tenant.company,
        } if d.tenant else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("")
def list_deals(
    stage: Optional[DealStage] = None,
    listing_id: Optional[int] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = db.query(Deal).options(joinedload(Deal.listing), joinedload(Deal.tenant))

    # Filter based on user role
    if user.role.value == "tenant":
        query = query.filter(Deal.tenant_id == user.id)
    elif user.role.value == "broker":
        query = query.filter(Deal.broker_id == user.id)
    elif user.role.value == "landlord":
        query = query.join(Listing).filter(Listing.property.has(owner_id=user.id))

    if stage:
        query = query.filter(Deal.stage == stage)
    if listing_id:
        query = query.filter(Deal.listing_id == listing_id)

    total = query.count()
    deals = query.order_by(Deal.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "deals": [deal_to_dict(d) for d in deals],
    }


@router.get("/pipeline")
def deal_pipeline(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get deal counts by stage for pipeline view."""
    query = db.query(Deal.stage, func.count(Deal.id))

    if user.role.value == "tenant":
        query = query.filter(Deal.tenant_id == user.id)
    elif user.role.value == "broker":
        query = query.filter(Deal.broker_id == user.id)
    elif user.role.value == "landlord":
        query = query.join(Listing).filter(Listing.property.has(owner_id=user.id))

    pipeline = query.group_by(Deal.stage).all()
    pipeline_dict = {stage.value: 0 for stage in DealStage}
    for stage, count in pipeline:
        pipeline_dict[stage.value] = count

    return {"pipeline": pipeline_dict}


@router.get("/{deal_id}")
def get_deal(deal_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    deal = db.query(Deal).options(joinedload(Deal.listing), joinedload(Deal.tenant)).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal_to_dict(deal)


@router.post("")
def create_deal(req: DealCreate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Update listing inquiry count
    listing.inquiry_count = (listing.inquiry_count or 0) + 1

    deal = Deal(
        listing_id=req.listing_id,
        tenant_id=user.id,
        broker_id=listing.broker_id,
        stage=DealStage.INQUIRY,
        proposed_price=req.proposed_price,
        proposed_area_sqm=req.proposed_area_sqm,
        lease_term_months=req.lease_term_months,
        notes=req.notes,
        activity_log=[{
            "action": "deal_created",
            "stage": "inquiry",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user.id,
        }],
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal_to_dict(deal)


@router.put("/{deal_id}")
def update_deal(deal_id: int, req: DealUpdate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    deal = db.query(Deal).options(joinedload(Deal.listing), joinedload(Deal.tenant)).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    now = datetime.now(timezone.utc)
    log_entry = {"timestamp": now.isoformat(), "user_id": user.id}

    if req.stage and req.stage != deal.stage:
        log_entry["action"] = "stage_changed"
        log_entry["from_stage"] = deal.stage.value
        log_entry["to_stage"] = req.stage.value
        deal.stage = req.stage

        # Set timeline dates based on stage
        if req.stage == DealStage.TOUR_SCHEDULED:
            deal.tour_date = now
        elif req.stage == DealStage.PROPOSAL:
            deal.proposal_date = now
        elif req.stage == DealStage.LOI_SIGNED:
            deal.loi_date = now
        elif req.stage == DealStage.SIGNED:
            deal.signed_date = now
            deal.final_price = req.final_price or deal.proposed_price
        elif req.stage in (DealStage.LOST, DealStage.WITHDRAWN):
            deal.lost_date = now
            deal.lost_reason = req.lost_reason
    else:
        log_entry["action"] = "deal_updated"

    if req.proposed_price is not None:
        deal.proposed_price = req.proposed_price
    if req.final_price is not None:
        deal.final_price = req.final_price
    if req.lease_term_months is not None:
        deal.lease_term_months = req.lease_term_months
    if req.notes is not None:
        deal.notes = req.notes

    activity_log = deal.activity_log or []
    activity_log.append(log_entry)
    deal.activity_log = activity_log

    db.commit()
    db.refresh(deal)
    return deal_to_dict(deal)
