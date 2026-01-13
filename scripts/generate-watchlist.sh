#!/bin/bash
# Generate investor watchlist

set -e

echo "Generating investor watchlist..."
docker-compose exec backend python3 app/cli.py generate-watchlist
