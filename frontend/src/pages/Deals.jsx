import { useState, useEffect } from 'react'
import { useAuth } from '../App'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const STAGES_HE = {
  inquiry: 'פנייה ראשונית',
  tour_scheduled: 'סיור תואם',
  tour_completed: 'סיור בוצע',
  proposal: 'הצעה',
  negotiation: 'משא ומתן',
  loi_signed: 'כתב כוונות',
  legal_review: 'בדיקה משפטית',
  signed: 'חוזה נחתם',
  lost: 'עסקה אבודה',
  withdrawn: 'בוטל',
}

const STAGE_COLORS = {
  inquiry: '#94a3b8', tour_scheduled: '#60a5fa', tour_completed: '#38bdf8',
  proposal: '#a78bfa', negotiation: '#f59e0b', loi_signed: '#fb923c',
  legal_review: '#f97316', signed: '#22c55e', lost: '#ef4444', withdrawn: '#6b7280',
}

const PIPELINE_STAGES = ['inquiry', 'tour_scheduled', 'tour_completed', 'proposal', 'negotiation', 'loi_signed', 'legal_review', 'signed']

export default function Deals() {
  const { user, token } = useAuth()
  const [deals, setDeals] = useState([])
  const [pipeline, setPipeline] = useState({})
  const [loading, setLoading] = useState(true)
  const [selectedStage, setSelectedStage] = useState(null)

  useEffect(() => {
    if (!token) { setLoading(false); return }
    Promise.all([
      fetch(`${API}/api/deals?page_size=50`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch(`${API}/api/deals/pipeline`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
    ]).then(([dealsData, pipelineData]) => {
      setDeals(dealsData.deals || [])
      setPipeline(pipelineData.pipeline || {})
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [token])

  const updateDealStage = (dealId, newStage) => {
    fetch(`${API}/api/deals/${dealId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ stage: newStage }),
    }).then(r => r.json()).then(updated => {
      setDeals(prev => prev.map(d => d.id === dealId ? updated : d))
    })
  }

  if (!user) return <div className="empty-state">יש להתחבר כדי לצפות בעסקאות</div>
  if (loading) return <div className="loading">טוען...</div>

  const filteredDeals = selectedStage ? deals.filter(d => d.stage === selectedStage) : deals

  return (
    <div className="deals-page">
      <div className="page-header">
        <h1>ניהול עסקאות</h1>
        <p className="subtitle">מעקב אחר כל העסקאות שלך</p>
      </div>

      {/* Pipeline View */}
      <div className="pipeline">
        <h3>צנרת עסקאות (Pipeline)</h3>
        <div className="pipeline-stages">
          {PIPELINE_STAGES.map(stage => (
            <div
              key={stage}
              className={`pipeline-stage ${selectedStage === stage ? 'active' : ''}`}
              style={{ borderColor: STAGE_COLORS[stage] }}
              onClick={() => setSelectedStage(selectedStage === stage ? null : stage)}
            >
              <div className="stage-count" style={{ backgroundColor: STAGE_COLORS[stage] }}>
                {pipeline[stage] || 0}
              </div>
              <div className="stage-name">{STAGES_HE[stage]}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Deals Table */}
      <div className="deals-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>נכס</th>
              <th>שלב</th>
              <th>מחיר מוצע</th>
              <th>תקופה (חודשים)</th>
              <th>תאריך פנייה</th>
              <th>פעולות</th>
            </tr>
          </thead>
          <tbody>
            {filteredDeals.map(d => (
              <tr key={d.id}>
                <td>{d.listing?.title_he || d.listing?.title || `מודעה #${d.listing_id}`}</td>
                <td>
                  <span className="stage-badge" style={{ backgroundColor: STAGE_COLORS[d.stage] }}>
                    {STAGES_HE[d.stage] || d.stage}
                  </span>
                </td>
                <td>{d.proposed_price ? `₪${d.proposed_price.toLocaleString()}` : '-'}</td>
                <td>{d.lease_term_months || '-'}</td>
                <td>{d.inquiry_date ? new Date(d.inquiry_date).toLocaleDateString('he-IL') : '-'}</td>
                <td>
                  <select
                    value={d.stage}
                    onChange={e => updateDealStage(d.id, e.target.value)}
                    className="stage-select"
                  >
                    {Object.entries(STAGES_HE).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
            {filteredDeals.length === 0 && (
              <tr><td colSpan={6} className="empty-cell">אין עסקאות להצגה</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
