import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Repo, RepoQueue, DeepSnapshot
from app.services.queue_manager import QueueManager


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestQueueManager:
    """Test queue prioritization logic."""

    def test_newly_eligible_priority(self, db_session):
        """Test that newly eligible repos get highest priority."""
        repo = Repo(
            github_id=12345,
            owner="test",
            name="test",
            full_name="test/test",
            stars=2500,
            forks=100,
            created_at=datetime(2024, 1, 1),
            pushed_at=datetime.utcnow(),
            archived=False,
            is_fork=False,
            eligible=True,
            first_discovered_at=datetime.utcnow() - timedelta(days=5)
        )
        db_session.add(repo)
        db_session.commit()

        queue_mgr = QueueManager(db_session)
        priority, reason = queue_mgr._calculate_priority(repo)

        assert priority == QueueManager.PRIORITY_NEW
        assert reason == "newly_eligible"

    def test_stale_priority(self, db_session):
        """Test that repos without recent analysis get stale priority."""
        repo = Repo(
            github_id=12345,
            owner="test",
            name="test",
            full_name="test/test",
            stars=2500,
            forks=100,
            created_at=datetime(2024, 1, 1),
            pushed_at=datetime.utcnow(),
            archived=False,
            is_fork=False,
            eligible=True,
            first_discovered_at=datetime.utcnow() - timedelta(days=100)
        )
        db_session.add(repo)
        db_session.commit()

        # No deep snapshot = stale
        queue_mgr = QueueManager(db_session)
        is_stale = queue_mgr._is_stale(repo.id)

        assert is_stale is True

    def test_queue_refresh(self, db_session):
        """Test queue refresh adds eligible repos."""
        repo1 = Repo(
            github_id=1,
            owner="test",
            name="repo1",
            full_name="test/repo1",
            stars=2500,
            forks=100,
            created_at=datetime(2024, 1, 1),
            pushed_at=datetime.utcnow(),
            archived=False,
            is_fork=False,
            eligible=True,
        )
        repo2 = Repo(
            github_id=2,
            owner="test",
            name="repo2",
            full_name="test/repo2",
            stars=3000,
            forks=150,
            created_at=datetime(2024, 1, 1),
            pushed_at=datetime.utcnow(),
            archived=False,
            is_fork=False,
            eligible=True,
        )
        db_session.add_all([repo1, repo2])
        db_session.commit()

        queue_mgr = QueueManager(db_session)
        stats = queue_mgr.refresh_queue()

        assert stats["added_to_queue"] == 2

        queue_items = db_session.query(RepoQueue).filter(RepoQueue.processed == False).all()
        assert len(queue_items) == 2

    def test_queue_summary(self, db_session):
        """Test queue summary statistics."""
        repo = Repo(
            github_id=1,
            owner="test",
            name="repo1",
            full_name="test/repo1",
            stars=2500,
            forks=100,
            created_at=datetime(2024, 1, 1),
            pushed_at=datetime.utcnow(),
            archived=False,
            is_fork=False,
            eligible=True,
        )
        db_session.add(repo)
        db_session.commit()

        queue_item = RepoQueue(
            repo_id=repo.id,
            priority=QueueManager.PRIORITY_NEW,
            priority_reason="newly_eligible",
            processed=False,
        )
        db_session.add(queue_item)
        db_session.commit()

        queue_mgr = QueueManager(db_session)
        summary = queue_mgr.get_queue_summary()

        assert summary["total_pending"] == 1
        assert summary["by_priority"]["newly_eligible"] == 1
