import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2']

export default function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [byCity, setByCity] = useState([])
  const [byType, setByType] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/analytics/overview`).then(r => r.json()),
      fetch(`${API}/api/analytics/by-city`).then(r => r.json()),
      fetch(`${API}/api/analytics/by-type`).then(r => r.json()),
    ]).then(([ov, city, type]) => {
      setOverview(ov)
      setByCity(city.cities || [])
      setByType(type.types || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">טוען נתונים...</div>

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>דשבורד שוק הנדל"ן המסחרי</h1>
        <p className="subtitle">סקירה כללית של שוק הנדל"ן המסחרי בישראל</p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-value">{overview?.total_properties || 0}</div>
          <div className="kpi-label">נכסים</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{overview?.total_active_listings || 0}</div>
          <div className="kpi-label">מודעות פעילות</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{(overview?.total_available_sqm || 0).toLocaleString()} מ"ר</div>
          <div className="kpi-label">שטח זמין</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">₪{(overview?.avg_price_ils || 0).toLocaleString()}</div>
          <div className="kpi-label">מחיר ממוצע</div>
        </div>
        <div className="kpi-card highlight">
          <div className="kpi-value">{overview?.active_deals || 0}</div>
          <div className="kpi-label">עסקאות פעילות</div>
        </div>
        <div className="kpi-card success">
          <div className="kpi-value">{overview?.signed_deals || 0}</div>
          <div className="kpi-label">עסקאות חתומות</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-grid">
        {byCity.length > 0 && (
          <div className="chart-card">
            <h3>מודעות לפי עיר</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byCity} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="city_he" type="category" width={100} />
                <Tooltip formatter={(v) => [v, 'מודעות']} />
                <Bar dataKey="listing_count" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {byType.length > 0 && (
          <div className="chart-card">
            <h3>התפלגות לפי סוג נכס</h3>
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
                  {byType.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>גישה מהירה</h3>
        <div className="action-grid">
          <Link to="/listings" className="action-card">
            <span className="action-icon">🔍</span>
            <span>חיפוש נכסים</span>
          </Link>
          <Link to="/properties" className="action-card">
            <span className="action-icon">🏗️</span>
            <span>ניהול נכסים</span>
          </Link>
          <Link to="/deals" className="action-card">
            <span className="action-icon">📋</span>
            <span>ניהול עסקאות</span>
          </Link>
          <Link to="/analytics" className="action-card">
            <span className="action-icon">📊</span>
            <span>אנליטיקס שוק</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
