import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function Watchlist() {
  const [watchlist, setWatchlist] = useState(null)
  const [sortBy, setSortBy] = useState('momentum')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadWatchlist(sortBy)
  }, [sortBy])

  const loadWatchlist = (track) => {
    setLoading(true)
    axios.get(`${API_BASE}/api/watchlist/latest?sort_by=${track}`)
      .then(res => {
        setWatchlist(res.data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }

  const handleExport = () => {
    window.open(`${API_BASE}/api/watchlist/export?sort_by=${sortBy}`, '_blank')
  }

  if (loading) return <div className="loading">Loading watchlist...</div>

  if (!watchlist || watchlist.total === 0) {
    return (
      <div className="watchlist">
        <h1>Investor Watchlist</h1>
        <div className="no-watchlist">
          <p>No watchlist available yet.</p>
          <p className="hint">Run the weekly watchlist generation job to populate this view.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="watchlist">
      <section className="watchlist-header">
        <h1>Investor Watchlist</h1>
        <p className="subtitle">Early signal discovery • Three-track ranking</p>
        <p className="last-update">Generated: {new Date(watchlist.watchlist_date).toLocaleDateString()}</p>
      </section>

      <section className="track-selector">
        <div className="track-buttons">
          <button
            className={sortBy === 'momentum' ? 'active' : ''}
            onClick={() => setSortBy('momentum')}
          >
            Momentum
          </button>
          <button
            className={sortBy === 'durability' ? 'active' : ''}
            onClick={() => setSortBy('durability')}
          >
            Durability
          </button>
          <button
            className={sortBy === 'adoption' ? 'active' : ''}
            onClick={() => setSortBy('adoption')}
          >
            Adoption
          </button>
        </div>
        <button className="export-btn" onClick={handleExport}>
          Export JSON
        </button>
      </section>

      <section className="track-explanation">
        <h3>Understanding the Tracks</h3>
        <div className="tracks-grid">
          <div className="track-card">
            <h4>Momentum</h4>
            <p>Growth velocity, star acceleration, activity spikes</p>
          </div>
          <div className="track-card">
            <h4>Durability</h4>
            <p>Contributor health, responsiveness, bus factor</p>
          </div>
          <div className="track-card">
            <h4>Adoption</h4>
            <p>Usage signals, dependents, fork-to-star ratio</p>
          </div>
        </div>
      </section>

      <section className="watchlist-table">
        <h2>Top Repos by {sortBy.charAt(0).toUpperCase() + sortBy.slice(1)} ({watchlist.total})</h2>
        <table>
          <thead>
            <tr>
              <th>Repository</th>
              <th>Language</th>
              <th>Stars</th>
              <th>Momentum</th>
              <th>Durability</th>
              <th>Adoption</th>
              <th>Rationale</th>
            </tr>
          </thead>
          <tbody>
            {watchlist.repos.map((repo, idx) => (
              <tr key={idx}>
                <td>
                  <Link to={`/repos/${repo.full_name.split('/')[0]}/${repo.full_name.split('/')[1]}`} className="repo-link">
                    {repo.full_name}
                  </Link>
                </td>
                <td>{repo.language || 'N/A'}</td>
                <td>{repo.stars.toLocaleString()}</td>
                <td className="score">{repo.scores.momentum.toFixed(1)}</td>
                <td className="score">{repo.scores.durability.toFixed(1)}</td>
                <td className="score">{repo.scores.adoption.toFixed(1)}</td>
                <td className="rationale">{repo.rationale}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="watchlist-integrity">
        <h3>Data Integrity</h3>
        <p>Scores computed from transparent three-track algorithm.</p>
        <p>Missing data (dependents, downloads) reduces adoption score but doesn't disqualify repos.</p>
        <p>Rationales explain why each repo surfaced on this watchlist.</p>
      </section>
    </div>
  )
}
