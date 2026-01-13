import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function UniverseOverview() {
  const [stats, setStats] = useState(null)
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE}/api/universe/stats`),
      axios.get(`${API_BASE}/api/universe/repos?limit=50`)
    ]).then(([statsRes, reposRes]) => {
      setStats(statsRes.data)
      setRepos(reposRes.data.repos)
      setLoading(false)
    }).catch(err => {
      console.error(err)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div className="universe-overview">
      <section className="hero">
        <h1>GitHub OSS Health</h1>
        <p className="subtitle">Research-grade system for early signal discovery</p>
      </section>

      {stats && (
        <section className="stats-grid">
          <div className="stat-card">
            <h3>{stats.counts.eligible_repos}</h3>
            <p>Eligible Repos</p>
          </div>
          <div className="stat-card">
            <h3>{stats.universe_criteria.min_stars}+</h3>
            <p>Minimum Stars</p>
          </div>
          <div className="stat-card">
            <h3>{stats.universe_criteria.max_age_months}mo</h3>
            <p>Maximum Age</p>
          </div>
        </section>
      )}

      {stats?.last_update && (
        <section className="last-update">
          <p>Last Discovery: {new Date(stats.last_update.discovery).toLocaleDateString()}</p>
          {stats.last_update.deep_analysis && (
            <p>Last Deep Analysis: {new Date(stats.last_update.deep_analysis).toLocaleDateString()}</p>
          )}
        </section>
      )}

      <section className="repos-table">
        <h2>Top Repos</h2>
        <table>
          <thead>
            <tr>
              <th>Repository</th>
              <th>Language</th>
              <th>Stars</th>
              <th>Forks</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {repos.map(repo => (
              <tr key={repo.id}>
                <td>
                  <Link to={`/repos/${repo.owner}/${repo.name}`}className="repo-link">
                    {repo.full_name}
                  </Link>
                </td>
                <td>{repo.language || 'N/A'}</td>
                <td>{repo.stars.toLocaleString()}</td>
                <td>{repo.forks.toLocaleString()}</td>
                <td>{new Date(repo.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
