#!/bin/bash
# ChatBI Quick Deploy Script
set -e

echo "🚀 ChatBI Quick Deploy"
echo "======================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found, copying from .env.example"
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
    echo "   Especially: LLM_API_KEY, JWT_SECRET_KEY"
    read -p "Press Enter to continue after editing .env..."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

echo "🐳 Building Docker image..."
docker build -t chatbi:latest .

echo "🔧 Starting services..."
cd docker
docker compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Health check..."
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ ChatBI is running!"
    echo ""
    echo "📍 Access URLs:"
    echo "   Frontend: http://localhost:8080"
    echo "   API Docs: http://localhost:8080/api/docs"
    echo "   Health:   http://localhost:8080/api/health"
    echo ""
    echo "🔐 Default Admin:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "📊 View logs:"
    echo "   docker compose -f docker/compose.yml logs -f chatbi-app"
else
    echo "⚠️  Service not responding yet, check logs:"
    echo "   docker compose -f docker/compose.yml logs chatbi-app"
fi
