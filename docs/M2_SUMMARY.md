# M2 Summary: Deep Analysis Metrics + Queue Logic

## What Was Built

### 1. Deep Analysis Service
Computes expensive, per-repo behavioral metrics:

**A) Contributor Health**
- Monthly active contributors over last 6 months
- Contribution distribution (top contributor share, top 5 share)
- Uses GitHub stats API (cached by GitHub, cheap)

**B) Velocity & Trend**
- Weekly commits, PRs, issues over last 12 weeks
- Trend slopes (linear regression)
- Uses commit activity stats + search API

**C) Responsiveness**
- Median time to first maintainer response (issues + PRs)
- Maintainer identified via author_association: OWNER, MEMBER, COLLABORATOR
- Samples last 30 closed issues/PRs

**D) Adoption Signals**
- Fork-to-star ratio (implemented)
- Dependents count (not yet implemented - requires additional API)
- npm downloads (not yet implemented - requires package name detection + npm API)

**E) Community Risk**
- Top contributor share (from distribution)
- Gini coefficient (placeholder - needs full contribution list)
- Active maintainers count

### 2. Queue Manager with Priority System
Priority levels (higher = more urgent):
- **10**: Newly eligible repos (discovered < 14 days ago)
- **8**: High momentum (> 10 stars/day growth)
- **7**: Activity spikes (pushed within 3 days)
- **5**: Stale analysis (no deep analysis in 30+ days)
- **3**: Regular refresh

### 3. API Budget Management
- Tracks requests per job run
- Enforces `deep_analysis_max_requests_per_run` limit (default: 5000)
- Aborts gracefully when budget exhausted
- Persists stats in `job_runs` table

### 4. 30-Day Guarantee
- Stale repos (not analyzed in 30+ days) get priority 5
- Queue refresh after discovery ensures all eligible repos eventually get analyzed
- If budget prevents completion, next run continues from queue

## What You Can Conclude Now

### Newly Possible:
1. **Contributor dynamics**: See if project has healthy contributor base or is dominated by 1-2 people
2. **Activity trends**: Is project accelerating, stable, or declining in commits/PRs/issues?
3. **Maintainer engagement**: How quickly do maintainers respond to community?
4. **Basic adoption**: Fork-to-star ratio as proxy for developer interest
5. **Risk assessment**: Identify projects with high bus factor (top contributor dominance)

### Data Integrity (Maintained):
- Every metric includes `availability` status
- Missing data marked with reason
- No invented numbers
- All raw data stored in `metrics_json` for auditability

## API Cost Per Repo

Estimated calls per deep analysis:
- Contributor stats: ~2 calls (cached by GitHub)
- Weekly activity: ~25 calls (1 stats + 24 search queries for PRs/issues)
- Responsiveness: ~30-60 calls (1 issues list + comments for ~30 items)
- Adoption: ~1 call

**Total: ~60-90 calls per repo**

With 5000 call budget per run:
- Can analyze ~55-80 repos per bi-weekly run
- Rate limit: 5000/hour for authenticated GitHub API
- Bi-weekly schedule is safe for ~1000 repos in universe

## What Remains Unknown

### Not Yet Measured:
1. **True adoption**: Dependents from dependency graph, actual npm/pypi downloads
2. **Community health details**: Gini coefficient (needs full data), PR merge rate, issue close rate
3. **Code quality proxies**: Test coverage, documentation completeness
4. **Ecosystem integration**: Package registry presence, framework/platform adoption

### Why:
- Dependency graph API has strict limits and requires GraphQL
- npm API integration pending
- Some metrics require additional external APIs

## Testing

10 tests passing:
- 6 tests from M1 (models, GitHub client)
- 4 new tests for M2 (queue prioritization, stale detection, queue refresh)

## Next: M3

M3 will build the read-only dashboard and API:
- FastAPI endpoints for universe stats, repo detail, watchlist
- React frontend with Recharts
- Methodology page explaining limitations
- No authentication (public read-only)
