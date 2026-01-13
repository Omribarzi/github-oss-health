#!/bin/bash
# One-command dev environment startup

set -e

echo "Starting GitHub OSS Health development environment..."

# Check for .env file
if [ ! -f backend/.env ]; then
    echo "Creating .env from .env.example..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env with your GITHUB_TOKEN"
    exit 1
fi

# Start all services
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
