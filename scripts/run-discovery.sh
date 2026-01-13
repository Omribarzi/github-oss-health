#!/bin/bash
# Run discovery job

set -e

echo "Running discovery job..."
docker-compose exec backend python3 app/cli.py discovery
