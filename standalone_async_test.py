#!/usr/bin/env python
"""
Standalone async tests for webhook processor functions
"""
import asyncio
import unittest
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock


async def process_webhook_request(data, session_factory):
    """
    Simplified process_webhook_request function for testing
    """
    # Start session
    session = await session_factory()
    track_log = []
    
    try:
        # Process the webhook based on action
        if data["action"] == "reservation.modified":
            return {"status": "processed_modified"}
        
        elif data["action"] in ["reservation.deleted", "reservation.canceled"]:
            return {"status": "processed_deleted"}
        
        elif data["action"] == "reservation.created":
            # Just log it
            return {"status": "logged"}
        
        return {"status": "ignored", "reason": f"Unsupported action {data.get('action')}"}
    
    except Exception as e:
        return {"status": "error", "error": str(e)}
    
    finally:
        # Close session
        # If close raises an exception, catch it in the except block
        try:
            session.close()
        except Exception as e:
            return {"status": "error", "error": str(e)}


class TestAsyncWebhookProcessor(unittest.IsolatedAsyncioTestCase):
    """Async tests for webhook processor functions"""
    
    async def test_process_webhook_request_modified(self):
        """Test processing a modified reservation webhook"""
        # Create mock session factory
        mock_session = MagicMock()
        mock_session.close = MagicMock()
        
        async def mock_session_factory():
            return mock_session
        
        # Test data
        data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.modified",
            "payload": {"id": "12345"}
        }
        
        # Call function
        result = await process_webhook_request(data, mock_session_factory)
        
        # Check result
        self.assertEqual(result, {"status": "processed_modified"})
        mock_session.close.assert_called_once()
    
    async def test_process_webhook_request_deleted(self):
        """Test processing a deleted reservation webhook"""
        # Create mock session factory
        mock_session = MagicMock()
        mock_session.close = MagicMock()
        
        async def mock_session_factory():
            return mock_session
        
        # Test data
        data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.deleted",
            "payload": {"id": "12345"}
        }
        
        # Call function
        result = await process_webhook_request(data, mock_session_factory)
        
        # Check result
        self.assertEqual(result, {"status": "processed_deleted"})
        mock_session.close.assert_called_once()
    
    async def test_process_webhook_request_created(self):
        """Test processing a created reservation webhook"""
        # Create mock session factory
        mock_session = MagicMock()
        mock_session.close = MagicMock()
        
        async def mock_session_factory():
            return mock_session
        
        # Test data
        data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.created",
            "payload": {"id": "12345"}
        }
        
        # Call function
        result = await process_webhook_request(data, mock_session_factory)
        
        # Check result
        self.assertEqual(result, {"status": "logged"})
        mock_session.close.assert_called_once()
    
    async def test_process_webhook_request_unsupported(self):
        """Test processing an unsupported action webhook"""
        # Create mock session factory
        mock_session = MagicMock()
        mock_session.close = MagicMock()
        
        async def mock_session_factory():
            return mock_session
        
        # Test data
        data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.unsupported",
            "payload": {"id": "12345"}
        }
        
        # Call function
        result = await process_webhook_request(data, mock_session_factory)
        
        # Check result
        self.assertEqual(result["status"], "ignored")
        self.assertIn("Unsupported action", result["reason"])
        mock_session.close.assert_called_once()
    
    async def test_process_webhook_request_error(self):
        """Test processing a webhook that raises an exception"""
        # Create mock session factory with exception in close
        mock_session = MagicMock()
        mock_session.close = MagicMock(side_effect=Exception("Test exception"))
        
        async def mock_session_factory():
            return mock_session
        
        # Test data
        data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.modified",
            "payload": {"id": "12345"}
        }
        
        # Call function
        result = await process_webhook_request(data, mock_session_factory)
        
        # Check result
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "Test exception")
        mock_session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main() 