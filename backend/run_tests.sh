#!/bin/bash
# Run all tests with coverage report

echo "🧪 Running Fortune Trading QUAD Test Suite"
echo "==========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov pytest-mock

echo ""
echo "🔬 Running Unit Tests..."
pytest tests/unit -v --cov=app --cov-report=term-missing

echo ""
echo "🔗 Running Integration Tests..."
pytest tests/integration -v

echo ""
echo "📊 Generating Coverage Report..."
pytest tests/ --cov=app --cov-report=html --cov-report=xml

echo ""
echo "✅ Test suite complete!"
echo "📈 Coverage report: htmlcov/index.html"
