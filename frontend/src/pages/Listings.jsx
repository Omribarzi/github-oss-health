import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const CITIES_HE = {
  tel_aviv: 'תל אביב', jerusalem: 'ירושלים', haifa: 'חיפה', beer_sheva: 'באר שבע',
  ramat_gan: 'רמת גן', herzliya: 'הרצליה', petah_tikva: 'פתח תקווה', netanya: 'נתניה',
  rishon_lezion: 'ראשון לציון', ashdod: 'אשדוד', raanana: 'רעננה', kfar_saba: 'כפר סבא',
  modiin: 'מודיעין', rehovot: 'רחובות', holon: 'חולון', lod: 'לוד', other: 'אחר',
}

const TYPES_HE = {
  office: 'משרד', retail: 'מסחרי', industrial: 'תעשייה',
  logistics: 'לוגיסטיקה', coworking: 'חלל עבודה משותף', mixed_use: 'שימוש מעורב',
}

const LISTING_TYPES_HE = { lease: 'השכרה', sublease: 'השכרת משנה', sale: 'מכירה' }

export default function Listings() {
  const [listings, setListings] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    city: '', property_type: '', listing_type: '', min_price: '', max_price: '', min_area: '', max_area: '',
  })

  const fetchListings = () => {
    setLoading(true)
    const params = new URLSearchParams({ page, page_size: 20 })
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v) })
    fetch(`${API}/api/listings?${params}`)
      .then(r => r.json())
      .then(data => {
        setListings(data.listings || [])
        setTotal(data.total || 0)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => { fetchListings() }, [page])

  const handleFilter = (e) => {
    e.preventDefault()
    setPage(1)
    fetchListings()
  }

  return (
    <div className="listings-page">
      <div className="page-header">
        <h1>נכסים מסחריים להשכרה</h1>
        <p className="subtitle">{total} נכסים זמינים</p>
      </div>

      {/* Filters */}
      <form className="filters-bar" onSubmit={handleFilter}>
        <select value={filters.city} onChange={e => setFilters({ ...filters, city: e.target.value })}>
          <option value="">כל הערים</option>
          {Object.entries(CITIES_HE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.property_type} onChange={e => setFilters({ ...filters, property_type: e.target.value })}>
          <option value="">כל הסוגים</option>
          {Object.entries(TYPES_HE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.listing_type} onChange={e => setFilters({ ...filters, listing_type: e.target.value })}>
          <option value="">כל סוגי העסקה</option>
          {Object.entries(LISTING_TYPES_HE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <input type="number" placeholder="מחיר מינימום (₪)" value={filters.min_price}
          onChange={e => setFilters({ ...filters, min_price: e.target.value })} />
        <input type="number" placeholder="מחיר מקסימום (₪)" value={filters.max_price}
          onChange={e => setFilters({ ...filters, max_price: e.target.value })} />
        <input type="number" placeholder='שטח מינימום (מ"ר)' value={filters.min_area}
          onChange={e => setFilters({ ...filters, min_area: e.target.value })} />
        <button type="submit" className="btn-primary">חיפוש</button>
      </form>

      {loading ? (
        <div className="loading">טוען...</div>
      ) : (
        <>
          <div className="listings-grid">
            {listings.map(l => (
              <Link to={`/listings/${l.id}`} key={l.id} className="listing-card">
                <div className="listing-image">
                  {l.property?.images?.[0] ? (
                    <img src={l.property.images[0]} alt={l.title} />
                  ) : (
                    <div className="placeholder-img">🏢</div>
                  )}
                  <span className="listing-type-badge">{LISTING_TYPES_HE[l.listing_type] || l.listing_type}</span>
                </div>
                <div className="listing-info">
                  <h3>{l.title_he || l.title}</h3>
                  <div className="listing-location">
                    {l.property?.city_he || CITIES_HE[l.property?.city] || ''} {l.property?.neighborhood_he ? `- ${l.property.neighborhood_he}` : ''}
                  </div>
                  <div className="listing-details">
                    <span className="listing-price">₪{l.price?.toLocaleString()} / חודש</span>
                    <span className="listing-area">{l.available_area_sqm} מ"ר</span>
                  </div>
                  <div className="listing-tags">
                    <span className="tag">{l.property?.property_type_he || TYPES_HE[l.property?.property_type] || ''}</span>
                    {l.furnished && <span className="tag">מרוהט</span>}
                    {l.property?.has_elevator && <span className="tag">מעלית</span>}
                    {l.property?.has_parking && <span className="tag">חניה</span>}
                  </div>
                  <div className="listing-meta">
                    <span>{l.view_count || 0} צפיות</span>
                    <span>{l.inquiry_count || 0} פניות</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {listings.length === 0 && <div className="empty-state">לא נמצאו נכסים מתאימים</div>}

          {total > 20 && (
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>הקודם</button>
              <span>עמוד {page} מתוך {Math.ceil(total / 20)}</span>
              <button disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(p => p + 1)}>הבא</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
