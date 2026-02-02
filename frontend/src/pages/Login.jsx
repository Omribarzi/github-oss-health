import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const ROLES = [
  { value: 'tenant', label: 'שוכר' },
  { value: 'landlord', label: 'משכיר / בעל נכס' },
  { value: 'broker', label: 'מתווך' },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [isRegister, setIsRegister] = useState(false)
  const [form, setForm] = useState({
    email: '', password: '', full_name: '', full_name_he: '',
    phone: '', role: 'tenant', company: '', company_he: '',
  })
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login'
    const body = isRegister ? form : { email: form.email, password: form.password }

    try {
      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'שגיאה')
      login(data.access_token, data.user)
      navigate('/')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>{isRegister ? 'הרשמה' : 'כניסה'}</h1>
        <p className="login-subtitle">
          {isRegister ? 'צור חשבון חדש בפלטפורמת נדלן IL' : 'התחבר לחשבון שלך'}
        </p>

        {error && <div className="error-msg">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>אימייל</label>
            <input type="email" required value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="form-group">
            <label>סיסמה</label>
            <input type="password" required value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })} />
          </div>

          {isRegister && (
            <>
              <div className="form-group">
                <label>שם מלא</label>
                <input required value={form.full_name}
                  onChange={e => setForm({ ...form, full_name: e.target.value, full_name_he: e.target.value })} />
              </div>
              <div className="form-group">
                <label>טלפון</label>
                <input type="tel" value={form.phone}
                  onChange={e => setForm({ ...form, phone: e.target.value })} />
              </div>
              <div className="form-group">
                <label>תפקיד</label>
                <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                  {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>חברה</label>
                <input value={form.company_he}
                  onChange={e => setForm({ ...form, company: e.target.value, company_he: e.target.value })} />
              </div>
            </>
          )}

          <button type="submit" className="btn-primary full-width">
            {isRegister ? 'הרשמה' : 'כניסה'}
          </button>
        </form>

        <div className="login-toggle">
          <button onClick={() => { setIsRegister(!isRegister); setError('') }} className="btn-link">
            {isRegister ? 'כבר יש לך חשבון? התחבר' : 'אין לך חשבון? הירשם'}
          </button>
        </div>
      </div>
    </div>
  )
}
