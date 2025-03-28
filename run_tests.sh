#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install pytest if not already installed
pip install pytest pytest-asyncio

# Run tests
pytest api/tests/ -v 