# Deployment Guide

Production deployment using Render (backend), Neon (PostgreSQL), and Vercel (frontend).

## Architecture Overview

```
Frontend (Vercel) → Backend (Render) → Database (Neon PostgreSQL)
```

## Prerequisites

- GitHub account
- Render account (render.com)
- Neon account (neon.tech)
- Vercel account (vercel.com)
- GitHub Personal Access Token with `repo` scope

## Step 1: Database (Neon)

### Create Database

1. Go to https://console.neon.tech
2. Click "Create a project"
3. Project name: `github-oss-health`
4. Region: Choose closest to your users
5. PostgreSQL version: 15
6. Click "Create project"

### Get Connection String

1. In project dashboard, click "Connection string"
2. Copy the connection string (format: `postgresql://user:password@host/dbname`)
3. Save for later use

**Connection string format:**
```
postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require
```

## Step 2: Backend (Render)

### Create Web Service

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `github-oss-health`
4. Configure:
   - **Name**: `github-oss-health-api`
   - **Region**: Same as Neon
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"`

### Environment Variables

Add these in Render dashboard (Environment tab):

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | `postgresql://...` | From Neon |
| `GITHUB_TOKEN` | `ghp_...` | Your GitHub token |
| `ENVIRONMENT` | `production` | |
| `API_RATE_LIMIT_SAFETY_THRESHOLD` | `500` | Optional |
| `DEEP_ANALYSIS_MAX_REQUESTS_PER_RUN` | `5000` | Optional |

### Deploy

1. Click "Create Web Service"
2. Wait for build and deployment (~3-5 minutes)
3. Note the service URL: `https://github-oss-health-api.onrender.com`

### Verify

Visit `https://your-service.onrender.com/health` - should return `{"status": "healthy"}`

## Step 3: Frontend (Vercel)

### Deploy via Dashboard

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### Environment Variables

Add in Vercel dashboard (Settings → Environment Variables):

| Key | Value |
|-----|-------|
| `VITE_API_BASE` | `https://your-backend.onrender.com` |

### Deploy

1. Click "Deploy"
2. Wait for build (~1-2 minutes)
3. Note the deployment URL: `https://github-oss-health.vercel.app`

### Custom Domain (Optional)

1. In Vercel project → Settings → Domains
2. Add your custom domain
3. Configure DNS as instructed

## Step 4: Scheduled Jobs

Render doesn't have native cron jobs in free tier. Options:

### Option A: Render Cron Jobs (Paid)

1. Create new Cron Job in Render
2. Schedule: `0 0 * * 0` (weekly Sunday midnight)
3. Command: `python app/cli.py discovery && python app/cli.py refresh-queue`

### Option B: GitHub Actions (Free)

Add to `.github/workflows/scheduled-jobs.yml`:

```yaml
name: Scheduled Jobs

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly Sunday midnight UTC

jobs:
  discovery:
    runs-on: ubuntu-latest
    steps:
      - name: Run discovery
        run: |
          curl -X POST https://your-backend.onrender.com/admin/trigger-discovery \
            -H "X-Admin-Token: ${{ secrets.ADMIN_TOKEN }}"
```

### Option C: External Service

Use a service like cron-job.org or EasyCron to hit webhook endpoints.

## Step 5: Monitoring

### Render Monitoring

- Built-in metrics: CPU, memory, request rate
- Logs: View in Render dashboard → Logs tab
- Alerts: Configure in Render dashboard → Settings → Notifications

### Database Monitoring

- Neon dashboard shows:
  - Connection count
  - Storage usage
  - Query performance

### Application Monitoring

Add to backend (optional):

```python
# Sentry for error tracking
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")

# Logging
import logging
logging.basicConfig(level=logging.INFO)
```

## Environment-Specific Configuration

### Production Settings

Update `backend/app/config.py` for production:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Production-specific
    cors_origins: List[str] = ["https://your-frontend.vercel.app"]
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")
```

### Secrets Management

**DO NOT commit secrets to Git.**

- Local dev: `.env` file (gitignored)
- Production: Environment variables in Render/Vercel
- Rotation: Update in dashboards, no code changes needed

## Backup and Recovery

### Database Backups (Neon)

Neon includes:
- Automatic daily backups (retained 7 days free tier)
- Point-in-time recovery
- Branch feature for testing

### Manual Backup

```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

## Security Checklist

- [ ] GitHub token has minimal scopes (`repo` only)
- [ ] Database uses SSL (`?sslmode=require` in connection string)
- [ ] Environment variables not committed to Git
- [ ] CORS configured with actual frontend domain (not `*`)
- [ ] Rate limiting enabled on backend
- [ ] Secrets rotated periodically

## Scaling Considerations

### Backend Scaling

Render autoscaling (paid plans):
- Horizontal: Multiple instances
- Vertical: Larger instance types

### Database Scaling

Neon:
- Free tier: 10 GB storage, 1 branch
- Paid tiers: More storage, compute, branches

### Cost Optimization

Free tier limits:
- **Render**: 750 hours/month (1 service running continuously)
- **Neon**: 10 GB storage, compute included
- **Vercel**: 100 GB bandwidth

Expected costs for moderate usage (<1000 repos):
- **Database**: $0-20/month
- **Backend**: $0-7/month
- **Frontend**: $0
- **Total**: $0-27/month

## Troubleshooting

### Backend won't start

**Check logs in Render dashboard:**
- Migration failures: Database connection issue
- Import errors: Missing dependencies in `requirements.txt`
- Port binding: Don't hardcode port, use `$PORT` env var

### Database connection fails

**Verify:**
- Connection string format correct
- SSL mode required: `?sslmode=require`
- Database exists and is accessible
- IP allowlist (Neon allows all by default)

### Frontend can't reach backend

**Check:**
- `VITE_API_BASE` environment variable set correctly
- CORS configuration includes frontend domain
- Backend URL is HTTPS (not HTTP)

## Rollback Procedure

### Backend Rollback

1. In Render dashboard → Deploy tab
2. Click on previous successful deployment
3. Click "Rollback to this version"

### Database Rollback

1. In Neon dashboard → Branches
2. Create branch from backup point
3. Update `DATABASE_URL` to point to branch
4. Test, then promote branch to main

### Frontend Rollback

1. In Vercel dashboard → Deployments
2. Find previous deployment
3. Click "..." → "Promote to Production"

## Monitoring Checklist

Daily:
- [ ] Check Render logs for errors
- [ ] Verify scheduled jobs ran

Weekly:
- [ ] Review database storage usage
- [ ] Check API rate limit consumption
- [ ] Review job run stats in database

Monthly:
- [ ] Rotate GitHub token
- [ ] Review costs
- [ ] Check for security updates
