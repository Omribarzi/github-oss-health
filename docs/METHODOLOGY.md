# Methodology

Complete explanation of what we measure, what we don't, and why.

## Design Philosophy

**Credibility over features.** This system prioritizes intellectual honesty:

1. **Never invent missing data** - If we don't have it, we say so
2. **Every metric includes availability status** - No silent failures
3. **Limitations stated explicitly** - No false confidence
4. **Restraint as design** - Complexity only when necessary

## Universe Definition

We analyze public GitHub repositories meeting ALL criteria:

- `stars >= 2000`
- `created_at >= now() - 24 months` (sliding 24-month window)
- `archived = false`
- `fork = false`
- `pushed_at` within last 90 days (for deep analysis eligibility)

**Why these criteria:**
- 2000 stars: Meaningful traction, filters noise
- 24 months: Early-stage focus, not legacy projects
- Not archived/fork: Active, original work
- Recent push: Sign of ongoing development

**All languages included** - No bias toward specific ecosystems.

## Two-Stage Pipeline

### Stage A: Discovery (Weekly, Cheap)

**Goal:** Find all eligible repos, track universe changes

**Method:** GitHub Search API

**Cost:** ~1-10 API calls per run

**Stores:**
- Repo metadata (owner, name, stars, forks, language)
- Created/pushed timestamps
- Eligibility status
- Immutable snapshots

**Enables:**
- Universe size tracking
- Star growth velocity
- Entry/exit monitoring

### Stage B: Deep Analysis (Bi-weekly, Expensive)

**Goal:** Compute behavioral metrics per repo

**Method:** Multiple GitHub APIs + heuristics

**Cost:** ~60-90 API calls per repo

**Budget:** Hard limit of 5000 calls per run

**Prioritization:**
1. Newly eligible (priority 10)
2. High momentum (priority 8)
3. Activity spikes (priority 7)
4. Stale (no analysis in 30+ days, priority 5)
5. Regular refresh (priority 3)

**Guarantee:** Every eligible repo analyzed at least once per 30 days (budget permitting)

## Metrics: What We Measure

### 1. Contributor Health

**Monthly Active Contributors (6 months)**
- Source: GitHub stats API (commit activity)
- Method: Unique commit authors per ~4-week period
- Availability: High (cached by GitHub)
- Limitation: Approximate, not perfect monthly boundaries

**Contribution Distribution**
- Source: GitHub contributors stats API
- Metrics: Total contributors, top-1 share, top-5 share
- Availability: High
- Limitation: All-time, not time-windowed

**Why measure:** Healthy projects have growing, distributed contributor bases

### 2. Velocity & Trend

**Weekly Activity (12 weeks)**
- Commits: From commit activity API
- PRs opened: Search API queries
- Issues opened: Search API queries

**Trend Slopes**
- Method: Linear regression over 12 weeks
- Metrics: Commit slope, PR slope, issue slope
- Interpretation: Positive = accelerating, negative = declining

**Why measure:** Trends matter more than absolute numbers

### 3. Responsiveness

**Median Time to First Maintainer Response**
- Sample: Last 30 closed issues/PRs
- Maintainer: `author_association` in [OWNER, MEMBER, COLLABORATOR]
- Metrics: Median hours for issues, median hours for PRs
- Availability: Medium (depends on comment data)

**Why measure:** Fast response indicates engaged maintainers

### 4. Adoption Signals

**Fork-to-Star Ratio**
- Method: forks / stars
- Availability: Always available
- Interpretation: Higher = more developer adoption

**Dependents Count**
- Source: Dependency graph API
- Availability: Low (requires GraphQL, strict limits)
- Status: NOT YET IMPLEMENTED

**Package Downloads**
- Source: npm API (for JavaScript/TypeScript)
- Availability: Low (requires package name detection)
- Status: NOT YET IMPLEMENTED

**Why measure:** Usage is better than popularity

### 5. Community Risk

**Top Contributor Share**
- From contribution distribution
- Interpretation: Higher = higher bus factor risk

**Active Maintainers Count**
- From contributor stats
- Limitation: All-time, not recent activity

**Gini Coefficient**
- Status: NOT YET IMPLEMENTED
- Reason: Needs full distribution, not sample

**Why measure:** Single-person projects are risky

## Metrics: What We Don't Measure

### Code Quality

**Not measured:**
- Test coverage
- Documentation completeness
- Code complexity
- Security vulnerabilities

**Why not:**
- Requires cloning repos (expensive, slow)
- Language-specific tooling needed
- Outside scope of GitHub API

### Community Engagement

**Not measured:**
- Discord/Slack activity
- Conference mentions
- Blog post frequency
- Twitter/social metrics

**Why not:**
- External to GitHub
- Hard to aggregate reliably
- Not comparable across projects

### Commercial Adoption

**Not measured:**
- Enterprise customers
- Revenue/funding
- Job postings mentioning project

**Why not:**
- Not in public GitHub data
- Privacy concerns
- Unreliable proxy

## Investor Watchlist

### Three-Track Ranking

**Track 1: Momentum (0-100)**
- Star velocity (40%): Stars/day from recent snapshots
- Time to 2000 stars (30%): Faster = higher
- Activity trend (30%): Positive commit slope

**Track 2: Durability (0-100)**
- Active contributors (40%): More = better
- Bus factor (30%): Lower top-contributor share = better
- Responsiveness (30%): Faster median response = better

**Track 3: Adoption (0-100)**
- Dependents (50%): Log scale
- Downloads (30%): Log scale
- Fork-to-star ratio (20%): Higher = better

**Why three tracks:**
- No single "score" hides complexity
- Investors can weight based on thesis
- Transparent: all three visible

### Eligibility for Watchlist

Repos surface if:
- Created within 24 months
- Meets base criteria
- AND either:
  - Recently crossed 2000 stars (<30 days ago)
  - OR exceptional signals (high trend, many contributors, fast response)

**Why these rules:**
- Focus on newly interesting, not comprehensive
- Early signal discovery, not exhaustive coverage

## Data Integrity Rules

### 1. Never Invent Missing Data

If API returns null or fails:
- Store null
- Mark availability as "not_available"
- Provide reason

**Example:**
```json
{
  "median_issue_response_hours": null,
  "availability": "insufficient_data",
  "reason": "Not enough maintainer responses found"
}
```

### 2. Store Raw Data

Every snapshot includes `metrics_json` with:
- All raw counts
- API responses
- Calculation inputs

**Why:** Auditability, recomputation if formula changes

### 3. Immutable Snapshots

Once written, snapshots never change.

**Why:** Historical integrity, trend analysis

### 4. Explicit Availability

Every metric has status:
- `available` - Data exists and is complete
- `partial` - Some data missing
- `insufficient_data` - Not enough to compute
- `not_available` - API returned no data
- `error` - Computation failed

## Limitations (By Design)

### GitHub API Constraints

- **Rate limits:** 5000 calls/hour, affects analysis capacity
- **Stats API delays:** Can lag up to 24 hours
- **Search API limits:** Max 1000 results, pagination issues

### Selection Bias

- **Stars != quality:** Popular != good
- **Visibility bias:** Projects with marketing appear more
- **Ecosystem bias:** Some languages have different star patterns

### Temporal Limitations

- **Snapshot-based:** Not real-time
- **Windowed metrics:** 6 months, 12 weeks may miss longer trends
- **Recency bias:** Newer projects have less history

### Coverage Gaps

- **Private repos:** Not analyzed
- **Non-GitHub projects:** GitLab, Bitbucket excluded
- **Mirrors:** May double-count some projects

## How to Interpret Results

### High Stars ≠ Good Investment

Stars indicate visibility, not necessarily:
- Code quality
- Commercial viability
- Team competence
- Market timing

### Trends > Absolutes

A project with:
- 3000 stars, +50/day velocity
- May be more interesting than
- 10000 stars, -5/day velocity

### Missing Data Is Information

If dependents = null:
- Maybe young project
- Maybe ecosystem doesn't track
- Maybe low actual adoption

**Don't assume missing = zero.**

### Watchlist ≠ Recommendations

Watchlist repos merit human review, not automatic investment.

## Verification

### Reproducibility

All metric computations are:
- Documented in code
- Unit tested
- Deterministic (for given inputs)

### Auditability

Every snapshot stores:
- Raw API responses
- Computation timestamp
- Version of code used

### Transparency

All formulas public:
- Source code on GitHub
- Documentation in `/docs`
- No proprietary algorithms

## Questions This System Can Answer

✅ Which repos crossed 2000 stars recently?
✅ Which have accelerating commit activity?
✅ Which have distributed contributor bases?
✅ Which respond quickly to issues?
✅ How does this week's watchlist compare to last?

## Questions This System Cannot Answer

❌ Will this project succeed commercially?
❌ Is the code high quality?
❌ Is the team competent?
❌ What's the total addressable market?
❌ Should I invest in this project?

## Updates to Methodology

When methodology changes:
1. Document in Git commit
2. Update this file
3. Store version in snapshot
4. Keep old snapshots unchanged

**Current version:** 1.0.0 (as of v1.0.0 release)
