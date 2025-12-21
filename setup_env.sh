#!/bin/bash
# Virtual Environment Setup Script for Trading System
# This script creates and activates a virtual environment, then installs dependencies

set -e  # Exit on error

PROJECT_DIR="/home/zohra/Documents/Stock_analysis/trading-test"
VENV_DIR="$PROJECT_DIR/venv"

echo "========================================="
echo "Trading System - Environment Setup"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment already exists at: $VENV_DIR"
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi

echo ""
echo "To activate the virtual environment, run:"
echo ""
echo "    source venv/bin/activate"
echo ""
echo "After activation, install dependencies with:"
echo ""
echo "    pip install -r requirements.txt"
echo ""
echo "========================================="
