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

Current milestone: **M3** (Dashboard & API)

## Milestones

- [x] M1: DB schema + discovery pipeline (v0.1.0)
- [x] M2: Deep analysis metrics + queue logic (v0.2.0)
- [x] M3: Dashboard & API (v0.3.0)
- [ ] M4: Watchlist generation + JSON export
- [ ] M5: Docker + tests + CI + fixtures mode
- [ ] M6: Deployment + runbook

## Quick Start

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app/main.py
```
Visit http://localhost:8000/docs for API documentation

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173 for dashboard

## Documentation

- [Methodology](docs/METHODOLOGY.md) - What we measure and what we don't
- [Deployment](docs/DEPLOYMENT.md) - Production setup guide
- [Development](docs/DEVELOPMENT.md) - Local development guide

## License

MIT
