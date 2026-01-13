#!/bin/bash
# Run deep analysis job

set -e

MAX_REPOS=${1:-10}

echo "Running deep analysis (max $MAX_REPOS repos)..."
docker-compose exec backend python3 app/cli.py deep-analysis --max-repos $MAX_REPOS
