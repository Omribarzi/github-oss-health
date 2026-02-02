import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2', '#84cc16', '#f43f5e']

const STAGES_HE = {
  inquiry: 'פנייה', tour_scheduled: 'סיור תואם', tour_completed: 'סיור בוצע',
  proposal: 'הצעה', negotiation: 'משא ומתן', loi_signed: 'כתב כוונות',
  legal_review: 'בדיקה משפטית', signed: 'נחתם', lost: 'אבוד', withdrawn: 'בוטל',
}

export default function Analytics() {
  const [byCity, setByCity] = useState([])
  const [byType, setByType] = useState([])
  const [dealPipeline, setDealPipeline] = useState(null)
  const [trends, setTrends] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/analytics/by-city`).then(r => r.json()),
      fetch(`${API}/api/analytics/by-type`).then(r => r.json()),
      fetch(`${API}/api/analytics/deal-pipeline`).then(r => r.json()),
      fetch(`${API}/api/analytics/price-trends`).then(r => r.json()),
    ]).then(([city, type, pipe, tr]) => {
      setByCity(city.cities || [])
      setByType(type.types || [])
      setDealPipeline(pipe)
      setTrends(tr.trends || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">טוען נתוני אנליטיקס...</div>

  const pipelineData = dealPipeline?.pipeline
    ? Object.entries(dealPipeline.pipeline)
        .filter(([k]) => !['lost', 'withdrawn'].includes(k))
        .map(([stage, count]) => ({ stage: STAGES_HE[stage] || stage, count }))
    : []

  return (
    <div className="analytics-page">
      <div className="page-header">
        <h1>אנליטיקס שוק</h1>
        <p className="subtitle">נתוני שוק הנדל"ן המסחרי בישראל</p>
      </div>

      {/* Pipeline Summary */}
      {dealPipeline && (
        <div className="analytics-summary">
          <div className="kpi-card">
            <div className="kpi-value">₪{(dealPipeline.total_pipeline_value_ils || 0).toLocaleString()}</div>
            <div className="kpi-label">שווי צנרת כולל</div>
          </div>
          <div className="kpi-card success">
            <div className="kpi-value">₪{(dealPipeline.signed_value_ils || 0).toLocaleString()}</div>
            <div className="kpi-label">שווי עסקאות חתומות</div>
          </div>
        </div>
      )}

      <div className="charts-grid">
        {/* Price by City */}
        {byCity.length > 0 && (
          <div className="chart-card">
            <h3>מחיר ממוצע לפי עיר (₪)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byCity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="city_he" />
                <YAxis />
                <Tooltip formatter={(v) => [`₪${v.toLocaleString()}`, 'מחיר ממוצע']} />
                <Bar dataKey="avg_price" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Listings by Type */}
        {byType.length > 0 && (
          <div className="chart-card">
            <h3>מודעות לפי סוג נכס</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={byType}
                  dataKey="listing_count"
                  nameKey="type_he"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ type_he, percent }) => `${type_he} (${(percent * 100).toFixed(0)}%)`}
                >
                  {byType.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Deal Pipeline */}
        {pipelineData.length > 0 && (
          <div className="chart-card">
            <h3>צנרת עסקאות</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pipelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Area by City */}
        {byCity.length > 0 && (
          <div className="chart-card">
            <h3>שטח זמין לפי עיר (מ"ר)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byCity} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="city_he" type="category" width={100} />
                <Tooltip formatter={(v) => [`${v.toLocaleString()} מ"ר`, 'שטח זמין']} />
                <Bar dataKey="total_area_sqm" fill="#059669" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Price Trends */}
        {trends.length > 0 && (
          <div className="chart-card full-width">
            <h3>מגמות מחירים לאורך זמן</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="avg_price_per_sqm" stroke="#2563eb" name='מחיר ממוצע למ"ר' />
                <Line type="monotone" dataKey="median_price_per_sqm" stroke="#7c3aed" name='מחיר חציון למ"ר' />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
