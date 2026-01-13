import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Repo, DiscoverySnapshot, JobRun


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestModels:
    """Test database models."""

    def test_repo_creation(self, db_session):
        """Test creating a repo record."""
        repo = Repo(
            github_id=12345,
            owner="test-owner",
            name="test-repo",
            full_name="test-owner/test-repo",
            language="Python",
            stars=2500,
            forks=100,
            created_at=datetime(2024, 1, 1),
            pushed_at=datetime(2025, 1, 1),
            archived=False,
            is_fork=False,
            eligible=True,
        )

        db_session.add(repo)
        db_session.commit()

        retrieved = db_session.query(Repo).filter(Repo.github_id == 12345).first()
        assert retrieved is not None
        assert retrieved.full_name == "test-owner/test-repo"
        assert retrieved.stars == 2500
        assert retrieved.eligible is True

    def test_discovery_snapshot(self, db_session):
        """Test creating a discovery snapshot."""
        repo = Repo(
            github_id=12345,
            owner="test",
            name="test",
            full_name="test/test",
            stars=2000,
            forks=50,
            created_at=datetime(2024, 1, 1),
            pushed_at=datetime(2025, 1, 1),
            archived=False,
            is_fork=False,
            eligible=True,
        )
        db_session.add(repo)
        db_session.commit()

        snapshot = DiscoverySnapshot(
            repo_id=repo.id,
            snapshot_date=datetime.utcnow(),
            stars=2000,
            forks=50,
            pushed_at=datetime(2025, 1, 1),
            eligible=True,
            snapshot_json={"test": "data"},
        )
        db_session.add(snapshot)
        db_session.commit()

        retrieved = db_session.query(DiscoverySnapshot).first()
        assert retrieved is not None
        assert retrieved.repo_id == repo.id
        assert retrieved.stars == 2000

    def test_job_run_tracking(self, db_session):
        """Test job run tracking."""
        job = JobRun(
            job_type="discovery",
            started_at=datetime.utcnow(),
            status="running",
            stats_json={"repos_found": 0},
        )
        db_session.add(job)
        db_session.commit()

        retrieved = db_session.query(JobRun).first()
        assert retrieved is not None
        assert retrieved.job_type == "discovery"
        assert retrieved.status == "running"
        assert "repos_found" in retrieved.stats_json
