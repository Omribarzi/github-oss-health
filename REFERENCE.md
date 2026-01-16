# GitHub OSS Health - Complete Reference

## What It Is
Investor analysis platform for early-stage open-source projects. Finds repos with 2000+ stars, <24 months old, ranks by Momentum, Durability, Adoption.

## Architecture
```
Discovery (Weekly) → Deep Analysis (Bi-weekly) → Watchlist
~1-10 API calls      ~60-90 calls/repo           3-track ranking
```

## Tech Stack
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: React 19 + Vite + Recharts
- Infra: Docker Compose, GitHub Actions

## Key Components
| Component | Purpose |
|-----------|---------|
| GitHubClient | Rate-limited API client, exponential backoff |
| DiscoveryService | Weekly broad search |
| DeepAnalysisService | 25+ metrics per repo |
| QueueManager | Priority-based scheduling |
| WatchlistGenerator | 3-track scoring |

## GitHub API Limits
- Core API: 5000/hour
- Search API: 30/hour
- Safety threshold: abort at 500 remaining

## Config
```python
api_rate_limit_safety_threshold = 500
deep_analysis_max_requests_per_run = 5000
min_stars = 2000
max_age_months = 24
```

## Security Implemented
- secrets.compare_digest() for tokens
- Production guard on /reset-database
- Security headers (XSS, clickjacking, HSTS)
- Rate limiting with slowapi

## Priority Queue
| Priority | Score | Criteria |
|----------|-------|----------|
| New | 10 | Discovered <14 days |
| High Momentum | 8 | >10 stars/day |
| Activity Spike | 7 | Pushed <3 days |
| Stale | 5 | No analysis 30+ days |

## For Founder Discovery

### Cheap Signals (1 API call)
- Account age vs first repo date
- First repo to hit 1000+ stars
- Solo maintainer pattern
- Bio keywords ("founder", "building")
- Empty company field = indie

### API Endpoints
```
GET /users/{username} - profile, age, followers
GET /users/{username}/repos - all repos
GET /repos/{owner}/{repo}/contributors - distribution
```

### Schema
```sql
CREATE TABLE founders (
  github_id BIGINT PRIMARY KEY,
  username VARCHAR(255),
  first_repo_hit_1k_at TIMESTAMP,
  is_solo_founder BOOLEAN,
  signal_score FLOAT
);

CREATE TABLE founder_snapshots (
  founder_id BIGINT REFERENCES founders,
  snapshot_date DATE,
  followers INT,
  total_stars INT,
  metrics_json JSONB
);
```

## Key Lessons
1. Two-stage pipeline saves API budget
2. Snapshot everything for trends
3. Search API only 30/hr - use for discovery only
4. GraphQL can batch queries
5. Track metric availability explicitly
