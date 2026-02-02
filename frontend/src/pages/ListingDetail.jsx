import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../App'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const PRICE_PERIODS_HE = {
  monthly: 'חודשי', annual: 'שנתי', per_sqm_monthly: 'למ"ר לחודש',
  per_sqm_annual: 'למ"ר לשנה', total: 'סה"כ',
}

export default function ListingDetail() {
  const { id } = useParams()
  const { user, token } = useAuth()
  const [listing, setListing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showInquiry, setShowInquiry] = useState(false)
  const [inquiryNote, setInquiryNote] = useState('')

  useEffect(() => {
    fetch(`${API}/api/listings/${id}`)
      .then(r => r.json())
      .then(data => { setListing(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [id])

  const handleInquiry = () => {
    if (!token) { alert('יש להתחבר כדי לשלוח פנייה'); return }
    fetch(`${API}/api/deals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ listing_id: parseInt(id), notes: inquiryNote }),
    })
      .then(r => r.json())
      .then(() => { alert('הפנייה נשלחה בהצלחה!'); setShowInquiry(false); setInquiryNote('') })
      .catch(() => alert('שגיאה בשליחת הפנייה'))
  }

  const handleFavorite = () => {
    if (!token) { alert('יש להתחבר כדי לשמור מועדפים'); return }
    fetch(`${API}/api/favorites/${id}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).then(r => r.json()).then(() => alert('נוסף למועדפים!'))
  }

  if (loading) return <div className="loading">טוען...</div>
  if (!listing) return <div className="empty-state">המודעה לא נמצאה</div>

  const prop = listing.property || {}

  return (
    <div className="listing-detail">
      <div className="detail-header">
        <div>
          <h1>{listing.title_he || listing.title}</h1>
          <p className="detail-location">
            {prop.city_he || ''} {prop.neighborhood_he ? `- ${prop.neighborhood_he}` : ''}
            {prop.street_address_he ? `, ${prop.street_address_he}` : ''}
          </p>
        </div>
        <div className="detail-actions">
          <button onClick={handleFavorite} className="btn-outline">שמור למועדפים</button>
          <button onClick={() => setShowInquiry(true)} className="btn-primary">שלח פנייה</button>
        </div>
      </div>

      {/* Image Gallery */}
      <div className="detail-gallery">
        {prop.images?.length > 0 ? (
          prop.images.map((img, i) => <img key={i} src={img} alt={`תמונה ${i + 1}`} />)
        ) : (
          <div className="placeholder-img large">🏢</div>
        )}
      </div>

      <div className="detail-grid">
        {/* Main Info */}
        <div className="detail-main">
          <section className="detail-section">
            <h2>פרטי הנכס</h2>
            {(listing.description_he || listing.description) && (
              <p className="detail-description">{listing.description_he || listing.description}</p>
            )}
            <div className="detail-specs">
              <div className="spec">
                <span className="spec-label">שטח</span>
                <span className="spec-value">{listing.available_area_sqm} מ"ר</span>
              </div>
              {listing.min_area_sqm && (
                <div className="spec">
                  <span className="spec-label">שטח מינימלי</span>
                  <span className="spec-value">{listing.min_area_sqm} מ"ר</span>
                </div>
              )}
              <div className="spec">
                <span className="spec-label">סוג נכס</span>
                <span className="spec-value">{prop.property_type_he || ''}</span>
              </div>
              {prop.building_class && (
                <div className="spec">
                  <span className="spec-label">דרגת בניין</span>
                  <span className="spec-value">Class {prop.building_class}</span>
                </div>
              )}
              <div className="spec">
                <span className="spec-label">שטח כולל הבניין</span>
                <span className="spec-value">{prop.total_area_sqm} מ"ר</span>
              </div>
              {prop.parking_spots > 0 && (
                <div className="spec">
                  <span className="spec-label">חניות</span>
                  <span className="spec-value">{prop.parking_spots}</span>
                </div>
              )}
            </div>
          </section>

          <section className="detail-section">
            <h2>מאפיינים</h2>
            <div className="features-grid">
              {prop.has_elevator && <span className="feature-tag">מעלית</span>}
              {prop.has_parking && <span className="feature-tag">חניה</span>}
              {listing.furnished && <span className="feature-tag">מרוהט</span>}
              {listing.condition && <span className="feature-tag">{listing.condition}</span>}
            </div>
          </section>

          {listing.min_lease_months && (
            <section className="detail-section">
              <h2>תנאי השכרה</h2>
              <div className="detail-specs">
                <div className="spec">
                  <span className="spec-label">תקופת שכירות מינימלית</span>
                  <span className="spec-value">{listing.min_lease_months} חודשים</span>
                </div>
                {listing.max_lease_months && (
                  <div className="spec">
                    <span className="spec-label">תקופת שכירות מקסימלית</span>
                    <span className="spec-value">{listing.max_lease_months} חודשים</span>
                  </div>
                )}
              </div>
            </section>
          )}
        </div>

        {/* Pricing Sidebar */}
        <div className="detail-sidebar">
          <div className="price-card">
            <div className="price-main">
              <span className="price-amount">₪{listing.price?.toLocaleString()}</span>
              <span className="price-period">{PRICE_PERIODS_HE[listing.price_period] || ''}</span>
            </div>
            {listing.management_fee_monthly && (
              <div className="price-extra">
                <span>דמי ניהול:</span>
                <span>₪{listing.management_fee_monthly.toLocaleString()} / חודש</span>
              </div>
            )}
            {listing.arnona_monthly && (
              <div className="price-extra">
                <span>ארנונה:</span>
                <span>₪{listing.arnona_monthly.toLocaleString()} / חודש</span>
              </div>
            )}
            {listing.negotiable && <div className="negotiable-badge">ניתן למשא ומתן</div>}
            <button onClick={() => setShowInquiry(true)} className="btn-primary full-width">שלח פנייה</button>
          </div>

          <div className="stats-card">
            <h4>סטטיסטיקות</h4>
            <div className="stat-row"><span>צפיות</span><span>{listing.view_count || 0}</span></div>
            <div className="stat-row"><span>פניות</span><span>{listing.inquiry_count || 0}</span></div>
            <div className="stat-row"><span>סיורים</span><span>{listing.tour_count || 0}</span></div>
          </div>
        </div>
      </div>

      {/* Inquiry Modal */}
      {showInquiry && (
        <div className="modal-overlay" onClick={() => setShowInquiry(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>שליחת פנייה</h2>
            <p>לגבי: {listing.title_he || listing.title}</p>
            <textarea
              placeholder="הערות נוספות..."
              value={inquiryNote}
              onChange={e => setInquiryNote(e.target.value)}
              rows={4}
            />
            <div className="modal-actions">
              <button onClick={() => setShowInquiry(false)} className="btn-outline">ביטול</button>
              <button onClick={handleInquiry} className="btn-primary">שלח</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
