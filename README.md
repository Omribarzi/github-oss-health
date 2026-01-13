# GitHub OSS Health & Early Signal Discovery System

Research-grade system for investor analysis of promising open-source projects.

## Project Philosophy

- **Credibility over features**: Every metric includes availability status and limitations
- **Restraint as design**: No invented data, no silent smoothing, no false certainty
- **Investor-focused**: Three-track analysis (Momentum, Durability, Adoption) for early signal discovery

## Universe Criteria

Analyzes public GitHub repositories that meet ALL:
- `stars >= 2000`
- `created_at >= now() - 24 months` (sliding window)
- `archived = false`
- `fork = false`
- `pushed_at` within last 90 days (for deep analysis)

## Architecture

- **Backend**: Python + FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **Frontend**: React + Vite + Recharts
- **Scheduler**: APScheduler (bi-weekly deep analysis, weekly discovery)
- **Queue**: Database-backed (`repo_queue` table)

## Development Status

Current milestone: **M5** (Docker + Tests + CI)

## Milestones

- [x] M1: DB schema + discovery pipeline (v0.1.0)
- [x] M2: Deep analysis metrics + queue logic (v0.2.0)
- [x] M3: Dashboard & API (v0.3.0)
- [x] M4: Watchlist generation + JSON export (v0.4.0)
- [x] M5: Docker + tests + CI (v0.5.0)
- [ ] M6: Deployment + runbook

## Quick Start

### One-Command Setup (Recommended)
```bash
# Copy env file and add your GitHub token
cp backend/.env.example backend/.env
# Edit backend/.env with your GITHUB_TOKEN

# Start everything
./scripts/start-dev.sh

# Services available at:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:5173
```

### Run Jobs
```bash
./scripts/run-discovery.sh              # Weekly discovery
./scripts/run-deep-analysis.sh 10       # Deep analysis (max 10 repos)
./scripts/generate-watchlist.sh         # Generate investor watchlist
./scripts/run-tests.sh                  # Run all tests
```

### Manual Setup (Without Docker)

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python3 app/main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Documentation

- [Methodology](docs/METHODOLOGY.md) - What we measure and what we don't
- [Deployment](docs/DEPLOYMENT.md) - Production setup guide
- [Development](docs/DEVELOPMENT.md) - Local development guide

## License

MIT
