import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function RepoDetail() {
  const { owner, repo } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API_BASE}/api/repos/${owner}/${repo}`)
      .then(res => {
        setData(res.data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [owner, repo])

  if (loading) return <div className="loading">Loading...</div>
  if (!data) return <div className="error">Repository not found</div>

  const { repo: repoData, latest_deep_analysis } = data

  return (
    <div className="repo-detail">
      <div className="breadcrumb">
        <Link to="/">Universe</Link> / {repoData.full_name}
      </div>

      <section className="repo-header">
        <h1>{repoData.full_name}</h1>
        <div className="repo-meta">
          <span>{repoData.language}</span>
          <span>★ {repoData.stars.toLocaleString()}</span>
          <span>{repoData.forks.toLocaleString()} forks</span>
        </div>
      </section>

      {latest_deep_analysis ? (
        <>
          <section className="metrics-grid">
            <div className="metric-card">
              <h3>Contributor Health</h3>
              {latest_deep_analysis.contributor_health.contribution_distribution ? (
                <>
                  <p><strong>Total Contributors:</strong> {latest_deep_analysis.contributor_health.contribution_distribution.total_contributors}</p>
                  <p><strong>Top 1 Share:</strong> {(latest_deep_analysis.contributor_health.contribution_distribution.top_1_share * 100).toFixed(1)}%</p>
                </>
              ) : (
                <p className="unavailable">Data not available</p>
              )}
            </div>

            <div className="metric-card">
              <h3>Responsiveness</h3>
              {latest_deep_analysis.responsiveness.median_issue_response_hours ? (
                <>
                  <p><strong>Median Issue Response:</strong> {latest_deep_analysis.responsiveness.median_issue_response_hours.toFixed(1)}h</p>
                  <p><strong>Median PR Response:</strong> {latest_deep_analysis.responsiveness.median_pr_response_hours?.toFixed(1) || 'N/A'}h</p>
                </>
              ) : (
                <p className="unavailable">Insufficient data ({latest_deep_analysis.responsiveness.availability})</p>
              )}
            </div>

            <div className="metric-card">
              <h3>Adoption</h3>
              <p><strong>Fork/Star Ratio:</strong> {latest_deep_analysis.adoption.fork_to_star_ratio?.toFixed(3) || 'N/A'}</p>
              <p className="unavailable">{latest_deep_analysis.adoption.availability}</p>
            </div>
          </section>

          {latest_deep_analysis.velocity.weekly_commits_12w && (
            <section className="chart-section">
              <h2>Activity Trend (12 weeks)</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={latest_deep_analysis.velocity.weekly_commits_12w.map((val, idx) => ({
                  week: idx + 1,
                  commits: val
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="commits" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            </section>
          )}
        </>
      ) : (
        <section className="no-deep-analysis">
          <p>Deep analysis not yet available for this repository.</p>
          <p className="hint">Repos are analyzed bi-weekly based on priority queue.</p>
        </section>
      )}

      <section className="data-integrity">
        <h3>Data Integrity</h3>
        <p>All metrics include availability status. Missing data is never invented.</p>
        <p><strong>Last Analysis:</strong> {latest_deep_analysis ? new Date(latest_deep_analysis.snapshot_date).toLocaleString() : 'Never'}</p>
      </section>
    </div>
  )
}
