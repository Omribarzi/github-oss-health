#!/usr/bin/env python3
"""
CLI for running discovery and deep analysis jobs.
"""
import argparse
import logging
from app.database import SessionLocal
from app.services.discovery import DiscoveryService

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
        return stats
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def run_deep_analysis():
    """Run deep analysis pipeline."""
    logger.info("Deep analysis not yet implemented (M2)")
    raise NotImplementedError("Deep analysis will be implemented in M2")


def main():
    parser = argparse.ArgumentParser(description="GitHub OSS Health CLI")
    parser.add_argument(
        "command",
        choices=["discovery", "deep-analysis"],
        help="Command to run"
    )

    args = parser.parse_args()

    if args.command == "discovery":
        run_discovery()
    elif args.command == "deep-analysis":
        run_deep_analysis()


if __name__ == "__main__":
    main()
