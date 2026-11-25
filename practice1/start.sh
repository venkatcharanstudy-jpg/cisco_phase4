#!/bin/bash

# CommerceHub Order Management API - Quick Start Guide

echo "============================================"
echo "CommerceHub Quick Start"
echo "============================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Check if dependencies are installed
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Check if database exists
echo ""
echo "Checking database..."
mysql -u admin -pAdmin123 -e "USE commercehub; SELECT COUNT(*) as tables FROM information_schema.TABLES WHERE TABLE_SCHEMA='commercehub';" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Setting up database..."
    python3 setup_db.py
else
    echo "✓ Database already exists"
fi

echo ""
echo "============================================"
echo "Starting FastAPI Application"
echo "============================================"
echo ""
echo "🚀 Server will start on: http://127.0.0.1:8000"
echo ""
echo "Available endpoints:"
echo "  - GET  http://127.0.0.1:8000/health"
echo "  - POST http://127.0.0.1:8000/orders"
echo "  - GET  http://127.0.0.1:8000/orders"
echo ""
echo "📚 Swagger UI: http://127.0.0.1:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start the application
uvicorn app.main:app --reload
