# Development Guide

Guide for local development and contributing.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- GitHub Personal Access Token

### Initial Setup

```bash
# Clone repository
git clone https://github.com/Omribarzi/github-oss-health.git
cd github-oss-health

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your GITHUB_TOKEN

# Start development environment
./scripts/start-dev.sh

# Services now running:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:5173
# - Database: localhost:5432
```

### Running Jobs

```bash
# Discovery (weekly job)
./scripts/run-discovery.sh

# Deep analysis (bi-weekly job)
./scripts/run-deep-analysis.sh 10  # Analyze max 10 repos

# Generate watchlist (weekly)
./scripts/generate-watchlist.sh

# Run tests
./scripts/run-tests.sh
```

## Project Structure

```
github-oss-health/
├── backend/                  # Python FastAPI backend
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   │   └── endpoints/   # Route handlers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   │   ├── discovery.py
│   │   │   ├── deep_analysis.py
│   │   │   ├── queue_manager.py
│   │   │   └── watchlist_generator.py
│   │   ├── utils/           # Utilities
│   │   ├── cli.py           # CLI commands
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # DB connection
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Database migrations
│   ├── tests/               # Unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── App.jsx          # Main app
│   │   └── App.css          # Styles
│   ├── Dockerfile
│   └── package.json
├── docs/                     # Documentation
├── scripts/                  # Helper scripts
├── docker-compose.yml
└── README.md
```

## Development Workflow

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes**
   - Backend: Edit files in `backend/app/`
   - Frontend: Edit files in `frontend/src/`
   - Hot reload automatically updates running services

3. **Test changes**
   ```bash
   ./scripts/run-tests.sh
   ```

4. **Commit using conventional commits**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # OR: fix:, docs:, test:, chore:
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   # Create PR on GitHub
   ```

### Adding a New Metric

Example: Add "PR merge rate" metric

1. **Update model** (`backend/app/models/deep_snapshot.py`):
   ```python
   pr_merge_rate = Column(Float, nullable=True)
   ```

2. **Create migration**:
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "add pr merge rate"
   docker-compose exec backend alembic upgrade head
   ```

3. **Add computation** (`backend/app/services/deep_analysis.py`):
   ```python
   def _calculate_pr_merge_rate(self, owner: str, repo: str) -> float:
       # Implementation
       pass
   ```

4. **Update snapshot save** (same file):
   ```python
   snapshot.pr_merge_rate = metrics.get("pr_merge_rate")
   ```

5. **Add to API response** (`backend/app/api/endpoints/repos.py`)

6. **Update frontend** (`frontend/src/pages/RepoDetail.jsx`)

7. **Test**:
   ```bash
   ./scripts/run-tests.sh
   ```

### Database Operations

**View logs:**
```bash
docker-compose logs db
```

**Connect to database:**
```bash
docker-compose exec db psql -U postgres -d github_oss_health
```

**Create migration:**
```bash
docker-compose exec backend alembic revision -m "description"
```

**Run migrations:**
```bash
docker-compose exec backend alembic upgrade head
```

**Rollback migration:**
```bash
docker-compose exec backend alembic downgrade -1
```

## Testing

### Running Tests

```bash
# All tests
./scripts/run-tests.sh

# Specific test file
docker-compose exec backend pytest tests/test_models.py -v

# With coverage
docker-compose exec backend pytest tests/ --cov=app --cov-report=html
```

### Writing Tests

Tests use in-memory SQLite for speed.

**Example:**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Repo

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_repo_creation(db_session):
    repo = Repo(
        github_id=123,
        owner="test",
        name="repo",
        full_name="test/repo",
        stars=2000,
        # ... other fields
    )
    db_session.add(repo)
    db_session.commit()

    assert db_session.query(Repo).count() == 1
```

## API Development

### Adding New Endpoint

1. **Create route** in `backend/app/api/endpoints/`:
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.database import get_db

   router = APIRouter()

   @router.get("/my-endpoint")
   def get_data(db: Session = Depends(get_db)):
       return {"data": "value"}
   ```

2. **Register router** in `backend/app/main.py`:
   ```python
   from app.api.endpoints import my_module
   app.include_router(my_module.router, prefix="/api/my", tags=["my"])
   ```

3. **Test manually**:
   ```bash
   curl http://localhost:8000/api/my/my-endpoint
   ```

4. **View auto-docs**: http://localhost:8000/docs

## Frontend Development

### Adding New Page

1. **Create component** in `frontend/src/pages/NewPage.jsx`:
   ```jsx
   export default function NewPage() {
     return <div><h1>New Page</h1></div>
   }
   ```

2. **Add route** in `frontend/src/App.jsx`:
   ```jsx
   import NewPage from './pages/NewPage'

   <Route path="/new" element={<NewPage />} />
   ```

3. **Add nav link**:
   ```jsx
   <Link to="/new">New</Link>
   ```

### Fetching Data

```jsx
import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function MyComponent() {
  const [data, setData] = useState(null)

  useEffect(() => {
    axios.get(`${API_BASE}/api/endpoint`)
      .then(res => setData(res.data))
      .catch(err => console.error(err))
  }, [])

  if (!data) return <div>Loading...</div>

  return <div>{/* render data */}</div>
}
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Database errors

```bash
# Reset database
docker-compose down -v  # CAUTION: Deletes all data
docker-compose up -d db
docker-compose exec backend alembic upgrade head
```

### Port conflicts

```bash
# Check what's using port 5432, 8000, or 5173
lsof -i :5432
lsof -i :8000
lsof -i :5173

# Kill process or change ports in docker-compose.yml
```

### Python dependency issues

```bash
# Rebuild backend
docker-compose build backend
docker-compose up -d backend
```

### Frontend won't load

```bash
# Check logs
docker-compose logs frontend

# Rebuild node_modules
docker-compose exec frontend npm install
docker-compose restart frontend
```

## Code Style

### Python (Backend)

- **Linter**: flake8
- **Line length**: 127 characters
- **Imports**: Grouped (stdlib, third-party, local)
- **Naming**: snake_case for functions/variables

**Run linter:**
```bash
docker-compose exec backend flake8 app
```

### JavaScript (Frontend)

- **Format**: Prettier (via Vite defaults)
- **Components**: Functional components with hooks
- **Naming**: PascalCase for components, camelCase for variables

## Performance

### Backend Optimization

- Database queries: Use indexes, avoid N+1
- API calls: Batch where possible, respect rate limits
- Caching: GitHub stats API responses cached by GitHub

### Frontend Optimization

- Code splitting: Use React.lazy() for large components
- Images: Optimize before adding
- API calls: Debounce user inputs

## Security

### Secrets

- **Never commit**: `.env` files, tokens, passwords
- **Development**: Use `.env.example` as template
- **Production**: Use environment variables

### API Keys

- **GitHub token**: Minimal scopes (`repo` only)
- **Rotation**: Update in `.env`, restart services

### Dependencies

```bash
# Check for vulnerabilities
docker-compose exec backend pip check
docker-compose exec frontend npm audit
```

## Debugging

### Backend

**Add print debugging:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Debug: {variable}")
```

**View logs:**
```bash
docker-compose logs -f backend
```

### Frontend

**Console logging:**
```javascript
console.log('Debug:', data)
```

**React DevTools**: Install browser extension

**View network**: Browser DevTools → Network tab

## Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Run linter
6. Submit PR

**PR Checklist:**
- [ ] Tests pass
- [ ] Linter passes
- [ ] Documentation updated
- [ ] Conventional commit messages
- [ ] No secrets in code

## Resources

- **FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Alembic**: https://alembic.sqlalchemy.org
- **React**: https://react.dev
- **Vite**: https://vitejs.dev
