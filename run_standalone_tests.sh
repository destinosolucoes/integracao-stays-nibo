#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install required packages if not already installed
pip install -q pytest pytest-asyncio fastapi httpx

echo "Running non-async tests..."
./standalone_test.py

echo ""
echo "Running async tests..."
./standalone_async_test.py

echo ""
echo "Running processor handles errors test..."
python -c "
import sys
import os
import asyncio
import unittest

parent_dir = os.path.abspath(os.path.join(os.getcwd()))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Mock modules to avoid DB connection issues
import unittest.mock
sys.modules['sqlalchemy'] = unittest.mock.MagicMock()
sys.modules['sqlmodel'] = unittest.mock.MagicMock()

from api.tests.test_webhook_queue_integration import TestQueueProcessorLifecycle

if __name__ == '__main__':
    unittest.main(defaultTest='TestQueueProcessorLifecycle.test_processor_handles_errors_and_continues')
"

echo ""
echo "All tests completed"
exit 0 