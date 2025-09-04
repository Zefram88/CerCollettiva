#!/bin/bash
# Test Docker environment for CerCollettiva

echo "🐳 Testing Docker Environment for CerCollettiva"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"

# Check Docker Compose configuration
echo "📋 Validating Docker Compose configuration..."
if docker-compose config > /dev/null 2>&1; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs media staticfiles
mkdir -p config/ssl
echo "✅ Directories created"

# Test building the web service
echo "🔨 Testing Docker build..."
if docker-compose build web > /dev/null 2>&1; then
    echo "✅ Docker build successful"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Test starting services (without full startup)
echo "🚀 Testing service startup..."
if docker-compose up -d db redis mqtt > /dev/null 2>&1; then
    echo "✅ Core services started successfully"
    
    # Wait a bit for services to be ready
    sleep 10
    
    # Check service health
    echo "🏥 Checking service health..."
    
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Services are running"
    else
        echo "⚠️ Some services may not be fully ready"
    fi
    
    # Stop services
    echo "🛑 Stopping test services..."
    docker-compose down
    echo "✅ Test services stopped"
    
else
    echo "❌ Failed to start core services"
    docker-compose down
    exit 1
fi

echo ""
echo "🎉 Docker environment test completed successfully!"
echo ""
echo "To start the full environment:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the environment:"
echo "  docker-compose down"
