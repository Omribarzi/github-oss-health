# M3 Summary: Dashboard & API

## What Was Built

### 1. FastAPI Backend (Read-Only)
**Endpoints:**
- `GET /api/universe/stats` - Universe overview (counts, criteria, language breakdown, last update)
- `GET /api/universe/repos` - Paginated repo list with filtering (language, star range, sort)
- `GET /api/repos/{owner}/{repo}` - Detailed repo view (basic info + latest snapshots)
- `GET /api/repos/{owner}/{repo}/history` - Historical snapshots (discovery or deep)

**Features:**
- CORS enabled for localhost development
- Pagination and filtering
- No authentication (public read-only)
- FastAPI automatic docs at `/docs`

### 2. React Dashboard (Vite + Recharts)
**Pages:**
- **Universe Overview** - Stats cards, language breakdown, top repos table
- **Repo Detail** - Metrics grid, activity charts, data integrity notes
- **Methodology** - Complete explanation of what we measure, what we don't, and why

**Design Principles:**
- Minimal, neutral aesthetic
- Trust-first messaging
- Data availability status visible
- No marketing copy
- No signup/login

### 3. Data Integrity Emphasis
Every view includes:
- Availability status for each metric
- "Data not available" vs "Insufficient data" messaging
- Explanation of limitations
- Raw snapshot dates

## What You Can Now Do

### Possible:
1. **Browse the universe** - See all eligible repos, filter by language/stars
2. **Inspect individual repos** - View all computed metrics with availability status
3. **Visualize trends** - Line charts for commit activity over 12 weeks
4. **Understand limitations** - Full methodology page explaining what's measured and what's not
5. **Track data freshness** - See when each repo was last analyzed

### Not Yet Possible:
1. **Watchlist / Deal Flow** - No investor-specific views yet (M4)
2. **Export data** - No JSON download (M4)
3. **Historical comparisons** - Charts show single snapshot, not time-series
4. **Admin functions** - No queue management UI
5. **Mobile-optimized** - Basic responsive but not mobile-first

## Testing

To test M3 locally:

```bash
# Backend
cd backend
python3 app/main.py
# Visit http://localhost:8000/docs

# Frontend
cd frontend
npm run dev
# Visit http://localhost:5173
```

## Design Choices

### Restraint Over Features
- No user accounts - public read-only system
- No "run your own analysis" - controlled pipeline only
- No self-serve data export yet
- No hidden scores or opaque rankings

### Trust Through Transparency
- Methodology page explains every limitation
- Missing data clearly marked, never invented
- Availability status for every metric
- Raw snapshot dates shown

### Investor-Focused (Not Developer-Focused)
- Not a "find cool projects" tool
- Not a social discovery platform
- Focus: early signal discovery for investment thesis

## What Remains for Production

### M4: Watchlist Generation
- Three-track ranking (Momentum, Durability, Adoption)
- Weekly investor watchlist
- Rationales for why repos surfaced
- JSON export

### M5: Docker + Tests
- docker-compose for local dev
- API integration tests
- Frontend build process
- One-command startup

### M6: Deployment
- Runbook for Render + Neon + Vercel
- Environment configuration
- Monitoring setup
- Token rotation process
