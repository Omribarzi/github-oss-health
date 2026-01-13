# M1 Summary: Database Schema + Discovery Pipeline

## What Was Built

### 1. Database Schema (SQLAlchemy + Alembic)
- **7 tables** with proper indexing and foreign keys:
  - `repos`: Core repository data
  - `discovery_snapshots`: Immutable time-series snapshots from weekly discovery
  - `deep_snapshots`: Deep analysis metrics (structure only, M2 will populate)
  - `repo_queue`: Priority queue for deep analysis scheduling
  - `investor_watchlists`: Three-track scoring for investor deal flow
  - `job_runs`: Job execution tracking with stats
  - `alerts`: System health alerts

### 2. GitHub API Client with Rate Limit Management
- Rate limit tracking from headers
- Safety threshold enforcement (aborts at 500 remaining calls)
- Exponential backoff for secondary rate limits
- Request counting and statistics
- Context manager support for proper cleanup

### 3. Discovery Pipeline
- **Universe criteria enforcement**:
  - `stars >= 2000`
  - `created_at >= now() - 24 months` (sliding window)
  - `archived = false`
  - `fork = false`
  - `pushed_at` within 90 days for eligibility
- GitHub Search API integration
- Upsert logic (update existing, insert new)
- Immutable snapshot creation
- Job run tracking with stats

## What You Can Conclude Now

### Possible:
1. **Identify the universe**: Run discovery to find all eligible repos
2. **Track growth**: Compare snapshots over time to see star growth, fork growth
3. **Monitor eligibility**: See which repos entered/exited the universe
4. **Assess data freshness**: Check `pushed_at` to see active vs. stale repos
5. **Basic statistics**: Count repos by language, star range, creation date

### Not Yet Possible:
1. **No behavioral metrics**: Can't assess contributor health, velocity, responsiveness (M2)
2. **No adoption signals**: Can't measure dependents, downloads (M2)
3. **No community risk**: Can't compute Gini coefficient, bus factor (M2)
4. **No watchlist**: Can't identify newly interesting repos (M4)
5. **No UI**: Can't browse or visualize data (M3)

## Data Integrity

All metrics include:
- `value`: The actual data
- `availability`: Whether data exists
- `snapshot_json`: Raw GitHub API response for auditability

Missing data is never invented. Eligibility is computed transparently and stored.

## Rate Limit Budget

Discovery is cheap:
- **1-10 requests per run** (depending on result pagination)
- Search API returns up to 1000 results
- No per-repo API calls in discovery

Safe to run weekly with standard GitHub API limits (5000/hour for authenticated requests).

## Next: M2

M2 will implement deep analysis:
- Per-repo metrics (expensive: ~10-50 API calls per repo)
- Queue prioritization
- 30-day guarantee (every eligible repo gets analyzed at least once per month)
- Budget enforcement
