#!/usr/bin/env python
import sys
import os
import pytest
from unittest.mock import patch

# Add the parent directory to sys.path to allow for importing the API modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Apply patch to sqlalchemy create_engine
@patch('sqlalchemy.create_engine')
def run_tests(mock_create_engine):
    # This will be called when sqlalchemy.create_engine is called
    # Return a mock engine that doesn't try to connect to MySQL
    from sqlalchemy.engine import Engine
    from unittest.mock import MagicMock
    mock_engine = MagicMock(spec=Engine)
    mock_create_engine.return_value = mock_engine
    
    # Run pytest with the provided arguments
    return pytest.main(['-v', os.path.dirname(__file__)])

if __name__ == '__main__':
    sys.exit(run_tests()) 