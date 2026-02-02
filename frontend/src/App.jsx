import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { useState, useEffect, createContext, useContext } from 'react'
import './App.css'
import Dashboard from './pages/Dashboard'
import Listings from './pages/Listings'
import ListingDetail from './pages/ListingDetail'
import Properties from './pages/Properties'
import Deals from './pages/Deals'
import Analytics from './pages/Analytics'
import Login from './pages/Login'

export const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}

function App() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(data => setUser(data))
        .catch(() => { setToken(null); localStorage.removeItem('token') })
    }
  }, [token])

  const login = (accessToken, userData) => {
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <Router>
        <div className="app" dir="rtl">
          <nav className="navbar">
            <div className="nav-container">
              <Link to="/" className="nav-logo">
                <span className="logo-text">נדלן IL</span>
              </Link>
              <div className="nav-links">
                <Link to="/">דשבורד</Link>
                <Link to="/listings">נכסים להשכרה</Link>
                <Link to="/properties">הנכסים שלי</Link>
                <Link to="/deals">עסקאות</Link>
                <Link to="/analytics">אנליטיקס</Link>
              </div>
              <div className="nav-auth">
                {user ? (
                  <div className="user-menu">
                    <span className="user-name">{user.full_name}</span>
                    <button onClick={logout} className="btn-logout">יציאה</button>
                  </div>
                ) : (
                  <Link to="/login" className="btn-login">כניסה</Link>
                )}
              </div>
            </div>
          </nav>

          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/listings" element={<Listings />} />
              <Route path="/listings/:id" element={<ListingDetail />} />
              <Route path="/properties" element={<Properties />} />
              <Route path="/deals" element={<Deals />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/login" element={<Login />} />
            </Routes>
          </main>

          <footer className="footer">
            <p>נדלן IL - פלטפורמת נדל"ן מסחרי בישראל</p>
          </footer>
        </div>
      </Router>
    </AuthContext.Provider>
  )
}

export default App
