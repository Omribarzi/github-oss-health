#!/bin/bash
# Run all tests

set -e

echo "Running tests..."

# Backend tests
echo "Backend tests..."
docker-compose exec backend pytest tests/ -v

echo ""
echo "✅ All tests passed!"
