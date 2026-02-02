from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.user import User
from app.models.listing import Listing
from app.models.favorite import Favorite
from app.models.property import CITY_NAMES_HE, PROPERTY_TYPE_NAMES_HE
from app.utils.auth import require_user

router = APIRouter()


@router.get("")
def list_favorites(user: User = Depends(require_user), db: Session = Depends(get_db)):
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id)
        .options(joinedload(Favorite.listing).joinedload(Listing.property))
        .order_by(Favorite.created_at.desc())
        .all()
    )

    return {
        "favorites": [
            {
                "id": f.id,
                "listing_id": f.listing_id,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "listing": {
                    "id": f.listing.id,
                    "title": f.listing.title,
                    "title_he": f.listing.title_he,
                    "price": f.listing.price,
                    "available_area_sqm": f.listing.available_area_sqm,
                    "city": f.listing.property.city.value if f.listing.property else None,
                    "city_he": CITY_NAMES_HE.get(f.listing.property.city, "") if f.listing.property else None,
                    "property_type": f.listing.property.property_type.value if f.listing.property else None,
                    "images": f.listing.property.images[:1] if f.listing.property and f.listing.property.images else [],
                } if f.listing else None,
            }
            for f in favorites
        ]
    }


@router.post("/{listing_id}")
def add_favorite(listing_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    existing = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.listing_id == listing_id).first()
    if existing:
        return {"message": "Already in favorites", "id": existing.id}

    fav = Favorite(user_id=user.id, listing_id=listing_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return {"message": "Added to favorites", "id": fav.id}


@router.delete("/{listing_id}")
def remove_favorite(listing_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.listing_id == listing_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(fav)
    db.commit()
    return {"message": "Removed from favorites"}
