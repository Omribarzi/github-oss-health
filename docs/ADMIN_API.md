# Admin API Documentation

HTTP endpoints for triggering data collection jobs remotely.

## Purpose

The Admin API allows you to trigger data collection jobs via HTTP requests instead of shell access. This enables:

- **Scheduled automation** via GitHub Actions or external cron services
- **Manual triggering** from anywhere with internet access
- **No shell access required** - works on free-tier hosting
- **Secure** - protected by API key authentication

## Security

All admin endpoints require authentication via the `X-Admin-Token` header.

### Setup

1. **Generate a secure API key**:
   ```bash
   openssl rand -hex 32
   ```

2. **Add to Render environment variables**:
   - Go to Render dashboard → Your service → Environment
   - Add: `ADMIN_API_KEY` = `<your-generated-key>`
   - Save changes (service will redeploy)

3. **Add to GitHub Secrets** (for automated jobs):
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Add secret: `ADMIN_API_KEY` = `<same-key-as-above>`

## Endpoints

Base URL: `https://github-oss-health.onrender.com`

### 1. Trigger Discovery

**Endpoint**: `POST /admin/trigger-discovery`

**Purpose**: Find all eligible repos matching universe criteria

**What it does**:
- Searches GitHub for repos with stars >= 2000, created in last 24 months
- Updates repo metadata (stars, forks, language)
- Automatically refreshes the analysis queue

**Example**:
```bash
curl -X POST "https://github-oss-health.onrender.com/admin/trigger-discovery" \
  -H "X-Admin-Token: your_api_key_here"
```

**Response**:
```json
{
  "status": "completed",
  "job_type": "discovery",
  "stats": {
    "repos_found": 150,
    "newly_eligible": 5,
    "newly_ineligible": 2
  },
  "queue_stats": {
    "total_queued": 150,
    "priority_breakdown": {...}
  },
  "message": "Discovery completed and queue refreshed successfully"
}
```

**When to run**: Weekly (every Sunday recommended)

---

### 2. Trigger Deep Analysis

**Endpoint**: `POST /admin/trigger-deep-analysis?max_repos=<N>`

**Purpose**: Analyze top-priority repos with detailed metrics

**What it does**:
- Analyzes repos from the priority queue (highest priority first)
- Computes: contributor health, velocity, responsiveness, adoption signals
- Respects GitHub API rate limits

**Parameters**:
- `max_repos` (optional): Maximum repos to analyze (1-100, default: 10)

**Example**:
```bash
curl -X POST "https://github-oss-health.onrender.com/admin/trigger-deep-analysis?max_repos=20" \
  -H "X-Admin-Token: your_api_key_here"
```

**Response**:
```json
{
  "status": "completed",
  "job_type": "deep_analysis",
  "max_repos": 20,
  "stats": {
    "repos_analyzed": 20,
    "repos_skipped": 0,
    "api_calls_used": 1200,
    "duration_seconds": 180
  },
  "message": "Analyzed 20 repos successfully"
}
```

**When to run**: Bi-weekly or after discovery

**Note**: Takes 10-20 minutes for 20 repos due to API rate limits

---

### 3. Trigger Watchlist Generation

**Endpoint**: `POST /admin/trigger-watchlist`

**Purpose**: Generate weekly investor watchlist with three-track rankings

**What it does**:
- Computes Momentum, Durability, and Adoption scores (0-100 each)
- Generates plain-English rationales
- Creates weekly snapshot

**Example**:
```bash
curl -X POST "https://github-oss-health.onrender.com/admin/trigger-watchlist" \
  -H "X-Admin-Token: your_api_key_here"
```

**Response**:
```json
{
  "status": "completed",
  "job_type": "watchlist",
  "stats": {
    "total_repos_considered": 150,
    "watchlist_entries": 50
  },
  "top_repos": [
    {
      "repo": "owner/name",
      "momentum_score": 95,
      "durability_score": 85,
      "adoption_score": 70
    }
  ],
  "message": "Watchlist generated successfully"
}
```

**When to run**: Weekly (after deep analysis)

---

### 4. Refresh Queue

**Endpoint**: `POST /admin/refresh-queue`

**Purpose**: Recalculate analysis priorities for all repos

**What it does**:
- Updates priority scores for all eligible repos
- Ensures newly eligible repos get highest priority
- Marks stale repos (>30 days since last analysis)

**Example**:
```bash
curl -X POST "https://github-oss-health.onrender.com/admin/refresh-queue" \
  -H "X-Admin-Token: your_api_key_here"
```

**When to run**: After discovery (or manually when needed)

---

### 5. Admin Status

**Endpoint**: `GET /admin/status`

**Purpose**: Check admin API configuration and health

**Example**:
```bash
curl "https://github-oss-health.onrender.com/admin/status" \
  -H "X-Admin-Token: your_api_key_here"
```

**Response**:
```json
{
  "status": "operational",
  "environment": "production",
  "configuration": {
    "min_stars": 2000,
    "max_age_months": 24,
    "api_rate_limit_safety_threshold": 500
  }
}
```

## Automated Scheduling with GitHub Actions

The repository includes a GitHub Actions workflow for weekly automation.

### Setup

1. **Add GitHub Secret**:
   - Go to repo → Settings → Secrets and variables → Actions
   - New secret: `ADMIN_API_KEY`
   - Value: Your admin API key

2. **Workflow runs automatically**:
   - Every Sunday at 00:00 UTC
   - Can also trigger manually from Actions tab

3. **Jobs run in sequence**:
   1. Discovery (finds repos)
   2. Deep Analysis (analyzes 20 repos)
   3. Watchlist Generation

### Manual Trigger

1. Go to GitHub repo → Actions tab
2. Select "Scheduled Data Collection" workflow
3. Click "Run workflow" → "Run workflow"

## Error Handling

### 401 Unauthorized
**Cause**: Missing `X-Admin-Token` header
**Fix**: Include header in request

### 403 Forbidden
**Cause**: Invalid API key
**Fix**: Check `ADMIN_API_KEY` in Render environment variables

### 503 Service Unavailable
**Cause**: `ADMIN_API_KEY` not configured on server
**Fix**: Add environment variable in Render dashboard

### 500 Internal Server Error
**Cause**: Job execution failed (database, API limits, etc.)
**Fix**: Check Render logs for details

## Security Best Practices

1. **Keep API key secret** - Never commit to Git
2. **Use GitHub Secrets** for automation
3. **Rotate key periodically** (quarterly recommended)
4. **Monitor usage** - Check Render logs for unauthorized attempts
5. **Use HTTPS only** - Never send key over HTTP

## Rate Limiting

The admin API itself has no rate limits, but be aware of:

- **GitHub API limits**: 5000 requests/hour
- **Deep analysis**: Respects safety threshold (500 calls remaining)
- **Job duration**: Deep analysis takes 10-20 minutes for 20 repos

## Troubleshooting

### Job times out
- **Deep analysis**: Reduce `max_repos` parameter
- **GitHub Actions**: Increase timeout (default 60 minutes is usually enough)

### API rate limit exhausted
- **Wait 1 hour** for GitHub API reset
- **Reduce max_repos** in deep analysis
- **Check logs** for unexpected API usage

### Database connection errors
- **Check Neon status**: https://neon.tech/status
- **Verify DATABASE_URL**: Render environment variables

## Example: Initial Data Population

Run these commands in order to populate your production database:

```bash
# Set your API key
API_KEY="your_api_key_here"
BASE_URL="https://github-oss-health.onrender.com"

# 1. Discovery (2-3 minutes)
curl -X POST "$BASE_URL/admin/trigger-discovery" \
  -H "X-Admin-Token: $API_KEY"

# 2. Deep analysis on 10 repos (10-15 minutes)
curl -X POST "$BASE_URL/admin/trigger-deep-analysis?max_repos=10" \
  -H "X-Admin-Token: $API_KEY"

# 3. Generate watchlist (< 1 minute)
curl -X POST "$BASE_URL/admin/trigger-watchlist" \
  -H "X-Admin-Token: $API_KEY"
```

Wait for each command to complete before running the next.

## Monitoring

Check job status via:

1. **Render logs**: Dashboard → Logs tab
2. **API response**: JSON response includes stats
3. **Frontend**: Visit https://github-oss-health.vercel.app to see data
4. **GitHub Actions**: Actions tab shows workflow run history

## Reference

- **Render Dashboard**: https://dashboard.render.com
- **Neon Dashboard**: https://console.neon.tech
- **GitHub Actions**: https://github.com/Omribarzi/github-oss-health/actions
- **API Docs**: https://github-oss-health.onrender.com/docs
