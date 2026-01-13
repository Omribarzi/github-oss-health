#!/usr/bin/env python3
"""
CLI for running discovery and deep analysis jobs.
"""
import argparse
import logging
from app.database import SessionLocal
from app.services.discovery import DiscoveryService
from app.services.deep_analysis import DeepAnalysisService
from app.services.queue_manager import QueueManager
from app.services.watchlist_generator import WatchlistGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def run_discovery():
    """Run discovery pipeline."""
    logger.info("Starting discovery job...")
    db = SessionLocal()
    try:
        service = DiscoveryService(db)
        stats = service.run()
        logger.info(f"Discovery completed successfully: {stats}")

        # Refresh queue after discovery
        logger.info("Refreshing queue...")
        queue_mgr = QueueManager(db)
        queue_stats = queue_mgr.refresh_queue()
        logger.info(f"Queue refreshed: {queue_stats}")

        return stats
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def run_deep_analysis(max_repos: int = None):
    """Run deep analysis pipeline."""
    logger.info("Starting deep analysis job...")
    db = SessionLocal()
    try:
        service = DeepAnalysisService(db)
        stats = service.run(max_repos=max_repos)
        logger.info(f"Deep analysis completed successfully: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Deep analysis failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def refresh_queue():
    """Refresh the queue priorities."""
    logger.info("Refreshing queue...")
    db = SessionLocal()
    try:
        queue_mgr = QueueManager(db)
        stats = queue_mgr.refresh_queue()
        summary = queue_mgr.get_queue_summary()
        logger.info(f"Queue stats: {stats}")
        logger.info(f"Queue summary: {summary}")
        return stats
    except Exception as e:
        logger.error(f"Queue refresh failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def generate_watchlist():
    """Generate weekly investor watchlist."""
    logger.info("Generating watchlist...")
    db = SessionLocal()
    try:
        generator = WatchlistGenerator(db)
        result = generator.generate_watchlist()
        logger.info(f"Watchlist generated: {result['stats']}")
        logger.info(f"Top repos: {result['watchlist'][:5]}")
        return result
    except Exception as e:
        logger.error(f"Watchlist generation failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="GitHub OSS Health CLI")
    parser.add_argument(
        "command",
        choices=["discovery", "deep-analysis", "refresh-queue", "generate-watchlist"],
        help="Command to run"
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=None,
        help="Maximum number of repos to analyze (deep-analysis only)"
    )

    args = parser.parse_args()

    if args.command == "discovery":
        run_discovery()
    elif args.command == "deep-analysis":
        run_deep_analysis(max_repos=args.max_repos)
    elif args.command == "refresh-queue":
        refresh_queue()
    elif args.command == "generate-watchlist":
        generate_watchlist()


if __name__ == "__main__":
    main()
