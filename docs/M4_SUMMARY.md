# M4 Summary: Watchlist Generation + JSON Export

## What Was Built

### 1. Three-Track Ranking Algorithm
Transparent scoring system with three independent dimensions:

**Track 1: Momentum (0-100)**
- Star velocity (40%): Stars per day from recent snapshots
- Time to 2000 stars (30%): Faster = higher score
- Activity trend (30%): Positive commit trend slope

**Track 2: Durability (0-100)**
- Active contributors count (40%): More = better
- Bus factor (30%): Lower top contributor share = higher score
- Responsiveness (30%): Faster median response time = higher score

**Track 3: Adoption (0-100)**
- Dependents count (50%): Log scale
- Package downloads (30%): Log scale (npm for now)
- Fork-to-star ratio (20%): Higher = more developer interest

### 2. Eligibility Criteria
Repos surface on watchlist if:
- Created within 24 months
- Meets base criteria (stars >= 2000, not archived, not fork)
- AND either:
  - Recently crossed 2000 stars (within 30 days)
  - OR exceptional signals (high commit trend, many contributors, fast response)

### 3. Watchlist Service
- `WatchlistGenerator` computes scores for eligible repos
- Generates 1-2 sentence rationales explaining why each repo surfaced
- Stores in `investor_watchlists` table with immutable snapshots
- CLI command: `python3 app/cli.py generate-watchlist`

### 4. API Endpoints
- `GET /api/watchlist/latest?sort_by=momentum` - Get latest watchlist sorted by track
- `GET /api/watchlist/export?sort_by=momentum` - Download JSON file
- `GET /api/watchlist/history` - List of generation dates

### 5. Dashboard Page
- Three-track selector buttons
- Top repos table with all three scores visible
- Rationales column explaining why each repo surfaced
- Export JSON button for offline analysis
- Explanation of what each track measures

## What You Can Now Do

### Newly Possible:
1. **Discover early-stage winners** - Find repos with strong signals before they're obvious
2. **Compare across dimensions** - Sort by momentum, durability, or adoption based on thesis
3. **Export for analysis** - Download JSON for custom analysis or CRM integration
4. **Understand rationales** - See transparent reasoning for why each repo surfaced
5. **Track over time** - Watchlist history shows evolution of interesting repos

### Investor Workflow:
1. View watchlist weekly (after generation job)
2. Sort by track matching investment thesis (e.g., durability for infrastructure plays)
3. Read rationales to understand signals
4. Click through to repo detail for deep metrics
5. Export JSON to share with investment committee

## Design Choices

### Three Tracks, Not One Score
- Avoids false precision of single composite score
- Lets investors apply their own weighting based on thesis
- Transparent: all three scores visible, not hidden

### Eligibility Tightly Constrained
- Only newly interesting repos (not the entire universe)
- Prevents watchlist from becoming overwhelming
- Focus on early signal discovery, not comprehensive coverage

### Rationales Required
- Every repo has plain-English explanation
- No "trust the algorithm" - show the reasoning
- Helps investors understand what signal triggered inclusion

## Scoring Transparency

Each track's formula is documented and configurable:
- `WatchlistGenerator._calculate_momentum_score()`
- `WatchlistGenerator._calculate_durability_score()`
- `WatchlistGenerator._calculate_adoption_score()`

Factors used to compute each score are stored in `metrics_snapshot.json` for auditability.

## Data Integrity Maintained

### Missing Data Handling:
- Adoption score heavily penalized when dependents/downloads unavailable
- But repos can still surface via momentum or durability
- Availability explicitly noted in factors

### No Invented Scores:
- If deep analysis missing, durability/adoption = 0
- Momentum can still be computed from discovery snapshots alone
- Rationale explains data availability

## What Remains

### Not Yet Implemented:
- **Scheduled generation** - Currently manual via CLI (will add APScheduler in M5)
- **Email/Slack notifications** - No alerting when new watchlist generated
- **Historical comparison UI** - Can't yet compare this week vs last week in dashboard
- **Saved searches/filters** - No personalization or saved investor preferences

### By Design Not Included:
- **User accounts** - Watchlist is public, not personalized
- **Custom weights** - Three tracks are fixed, investors choose which to sort by
- **Predictive scoring** - No ML, just transparent heuristics

## Testing

To test M4:
```bash
# Generate watchlist (requires repos in DB from M1-M2)
cd backend
python3 app/cli.py generate-watchlist

# View in API
curl http://localhost:8000/api/watchlist/latest?sort_by=momentum

# Download export
curl http://localhost:8000/api/watchlist/export -o watchlist.json

# View in dashboard
cd frontend
npm run dev
# Visit http://localhost:5173/watchlist
```

## Next: M5 (Docker + Tests)

M5 will add:
- Docker Compose for one-command local dev
- Full test suite with fixtures
- CI pipeline
- Sample mode for deterministic testing
