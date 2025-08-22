#!/bin/bash

echo "🐍 Setting up Python virtual environment for Local File Server"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies (none required for this project)
echo "📋 No external dependencies required - using Python built-in modules"

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "To run the server:"
echo "   python index.py"
echo ""
echo "To deactivate the virtual environment:"
echo "   deactivate"
