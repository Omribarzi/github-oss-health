import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import UniverseOverview from './pages/UniverseOverview'
import RepoDetail from './pages/RepoDetail'
import Methodology from './pages/Methodology'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-title">GitHub OSS Health</Link>
            <div className="nav-links">
              <Link to="/">Universe</Link>
              <Link to="/methodology">Methodology</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<UniverseOverview />} />
            <Route path="/repos/:owner/:repo" element={<RepoDetail />} />
            <Route path="/methodology" element={<Methodology />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>Research-grade investor analysis • Data integrity over completeness</p>
        </footer>
      </div>
    </Router>
  )
}

export default App
