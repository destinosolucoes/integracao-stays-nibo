import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock

# Add parent directory to path to allow imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.close = MagicMock()
    return session

@pytest.fixture
async def async_db_session_factory(mock_db_session):
    """Create an async factory function that returns a mock database session"""
    async def _factory():
        return mock_db_session
    return _factory

@pytest.fixture
def mock_nibo_api():
    """Create mock objects for Nibo API functions"""
    return {
        "create_credit_schedule": MagicMock(return_value={"id": "credit123"}),
        "create_debit_schedule": MagicMock(return_value={"id": "debit123"}),
        "get_credit_schedule": MagicMock(return_value=[]),
        "get_debit_schedule": MagicMock(return_value=[]),
        "update_credit_schedule": MagicMock(return_value={"id": "credit123", "updated": True}),
        "update_debit_schedule": MagicMock(return_value={"id": "debit123", "updated": True}),
        "delete_credit_schedule": MagicMock(return_value=True),
        "delete_debit_schedule": MagicMock(return_value=True),
    }

@pytest.fixture
def mock_stays_api():
    """Create mock objects for Stays API functions"""
    return {
        "get_reservation": MagicMock(return_value={}),
        "get_reservation_report": MagicMock(return_value={}),
        "get_listing": MagicMock(return_value={}),
        "get_client": MagicMock(return_value={}),
    } 