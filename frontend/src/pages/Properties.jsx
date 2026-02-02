import { useState, useEffect } from 'react'
import { useAuth } from '../App'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const CITIES = [
  { value: 'tel_aviv', label: 'תל אביב-יפו' }, { value: 'jerusalem', label: 'ירושלים' },
  { value: 'haifa', label: 'חיפה' }, { value: 'beer_sheva', label: 'באר שבע' },
  { value: 'ramat_gan', label: 'רמת גן' }, { value: 'herzliya', label: 'הרצליה' },
  { value: 'petah_tikva', label: 'פתח תקווה' }, { value: 'netanya', label: 'נתניה' },
  { value: 'rishon_lezion', label: 'ראשון לציון' }, { value: 'raanana', label: 'רעננה' },
  { value: 'kfar_saba', label: 'כפר סבא' }, { value: 'modiin', label: 'מודיעין' },
  { value: 'rehovot', label: 'רחובות' }, { value: 'other', label: 'אחר' },
]

const TYPES = [
  { value: 'office', label: 'משרד' }, { value: 'retail', label: 'מסחרי' },
  { value: 'industrial', label: 'תעשייה' }, { value: 'logistics', label: 'לוגיסטיקה' },
  { value: 'coworking', label: 'חלל עבודה משותף' }, { value: 'mixed_use', label: 'שימוש מעורב' },
]

export default function Properties() {
  const { user, token } = useAuth()
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '', name_he: '', description: '', description_he: '',
    property_type: 'office', city: 'tel_aviv', neighborhood_he: '', street_address_he: '',
    total_area_sqm: '', floor_count: '', year_built: '', parking_spots: 0,
    has_elevator: false, has_loading_dock: false, accessibility: false, building_class: '',
  })

  const fetchProperties = () => {
    setLoading(true)
    fetch(`${API}/api/properties?page_size=50`)
      .then(r => r.json())
      .then(data => { setProperties(data.properties || []); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { fetchProperties() }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!token) { alert('יש להתחבר'); return }
    const body = {
      ...form,
      total_area_sqm: parseFloat(form.total_area_sqm),
      floor_count: form.floor_count ? parseInt(form.floor_count) : null,
      year_built: form.year_built ? parseInt(form.year_built) : null,
      parking_spots: parseInt(form.parking_spots) || 0,
    }
    fetch(`${API}/api/properties`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(body),
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json() })
      .then(() => { setShowForm(false); fetchProperties() })
      .catch(() => alert('שגיאה ביצירת הנכס'))
  }

  return (
    <div className="properties-page">
      <div className="page-header">
        <h1>ניהול נכסים</h1>
        {user && <button onClick={() => setShowForm(true)} className="btn-primary">+ הוסף נכס</button>}
      </div>

      {loading ? <div className="loading">טוען...</div> : (
        <div className="properties-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>שם הנכס</th>
                <th>סוג</th>
                <th>עיר</th>
                <th>שטח (מ"ר)</th>
                <th>דרגה</th>
                <th>חניות</th>
                <th>יחידות</th>
              </tr>
            </thead>
            <tbody>
              {properties.map(p => (
                <tr key={p.id}>
                  <td><strong>{p.name_he || p.name}</strong></td>
                  <td>{p.property_type_he}</td>
                  <td>{p.city_he}</td>
                  <td>{p.total_area_sqm?.toLocaleString()}</td>
                  <td>{p.building_class || '-'}</td>
                  <td>{p.parking_spots || 0}</td>
                  <td>{p.units?.length || 0}</td>
                </tr>
              ))}
              {properties.length === 0 && (
                <tr><td colSpan={7} className="empty-cell">אין נכסים להצגה</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal wide" onClick={e => e.stopPropagation()}>
            <h2>הוספת נכס חדש</h2>
            <form onSubmit={handleSubmit} className="property-form">
              <div className="form-grid">
                <div className="form-group">
                  <label>שם הנכס (עברית)</label>
                  <input required value={form.name_he} onChange={e => setForm({ ...form, name_he: e.target.value, name: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>סוג נכס</label>
                  <select value={form.property_type} onChange={e => setForm({ ...form, property_type: e.target.value })}>
                    {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>עיר</label>
                  <select value={form.city} onChange={e => setForm({ ...form, city: e.target.value })}>
                    {CITIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>שכונה</label>
                  <input value={form.neighborhood_he} onChange={e => setForm({ ...form, neighborhood_he: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>כתובת</label>
                  <input value={form.street_address_he} onChange={e => setForm({ ...form, street_address_he: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>שטח כולל (מ"ר)</label>
                  <input required type="number" value={form.total_area_sqm} onChange={e => setForm({ ...form, total_area_sqm: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>קומות</label>
                  <input type="number" value={form.floor_count} onChange={e => setForm({ ...form, floor_count: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>שנת בנייה</label>
                  <input type="number" value={form.year_built} onChange={e => setForm({ ...form, year_built: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>חניות</label>
                  <input type="number" value={form.parking_spots} onChange={e => setForm({ ...form, parking_spots: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>דרגת בניין</label>
                  <select value={form.building_class} onChange={e => setForm({ ...form, building_class: e.target.value })}>
                    <option value="">-</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                  </select>
                </div>
              </div>
              <div className="form-checkboxes">
                <label><input type="checkbox" checked={form.has_elevator} onChange={e => setForm({ ...form, has_elevator: e.target.checked })} /> מעלית</label>
                <label><input type="checkbox" checked={form.has_loading_dock} onChange={e => setForm({ ...form, has_loading_dock: e.target.checked })} /> רמפת פריקה</label>
                <label><input type="checkbox" checked={form.accessibility} onChange={e => setForm({ ...form, accessibility: e.target.checked })} /> נגישות</label>
              </div>
              <div className="form-group full-width">
                <label>תיאור</label>
                <textarea value={form.description_he} onChange={e => setForm({ ...form, description_he: e.target.value, description: e.target.value })} rows={3} />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowForm(false)} className="btn-outline">ביטול</button>
                <button type="submit" className="btn-primary">שמור</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
