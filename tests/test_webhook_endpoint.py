#!/usr/bin/env python
"""
Tests for the webhook endpoint to ensure requests are added to the queue
"""
import sys
import os
import asyncio
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add the parent directory to sys.path to allow for importing the API modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Mock modules to avoid DB connection issues
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlmodel'] = MagicMock()
sys.modules['api.queue'] = MagicMock()
sys.modules['api.webhook_processor'] = MagicMock()

# Create test app
test_app = FastAPI()

# Create a custom async mock for add_to_queue that doesn't use asyncio.Future
class AsyncQueueMock:
    """Custom mock for async queue functions that doesn't rely on event loop"""
    def __init__(self):
        self.calls = []
    
    async def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return None


class TestWebhookEndpoint(unittest.TestCase):
    """Tests for the webhook endpoint"""
    
    def setUp(self):
        """Set up before each test"""
        # Patch the modules we need to mock
        self.mock_validate_header = patch('api.utils.validate_header').start()
        self.mock_validate_header.return_value = True
        
        self.mock_create_log = patch('api.utils.create_request_log').start()
        
        # Use our custom mock that doesn't need an event loop
        self.mock_add_to_queue = AsyncQueueMock()
        self.patcher = patch('api.queue.add_to_queue', self.mock_add_to_queue)
        self.patcher.start()
        
        # Create FastAPI test client
        from api.index import app
        self.client = TestClient(app)
    
    def tearDown(self):
        """Clean up after each test"""
        patch.stopall()
    
    def test_webhook_endpoint_adds_to_queue(self):
        """Test that the webhook endpoint adds requests to the queue"""
        # Create test data
        test_data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.created",
            "payload": {"id": "12345"}
        }
        
        # Call the webhook endpoint
        response = self.client.post(
            "/api/stays-webhook",
            json=test_data,
            headers={"x-stays-client-id": "test", "x-stays-signature": "test"}
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "queued"})
        
        # Verify add_to_queue was called with the right data
        self.assertEqual(len(self.mock_add_to_queue.calls), 1)
        # Get the first argument of the first call
        call_args = self.mock_add_to_queue.calls[0][0][0]
        self.assertEqual(call_args, test_data)
        
        # Verify create_request_log was called
        self.mock_create_log.assert_called_once()
    
    def test_webhook_endpoint_validates_header(self):
        """Test that the webhook endpoint validates the header"""
        # Set up mocks - header validation fails
        self.mock_validate_header.return_value = False
        
        # Create test data
        test_data = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.created",
            "payload": {"id": "12345"}
        }
        
        # Call the webhook endpoint
        response = self.client.post(
            "/api/stays-webhook",
            json=test_data,
            headers={"x-stays-client-id": "invalid", "x-stays-signature": "invalid"}
        )
        
        # Verify response - should be 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Verify add_to_queue was NOT called
        self.assertEqual(len(self.mock_add_to_queue.calls), 0)
        
        # Verify create_request_log was still called (should log even invalid requests)
        self.mock_create_log.assert_called_once()
    
    def test_webhook_endpoint_processes_different_actions(self):
        """Test that the webhook endpoint handles different action types"""
        # Test different action types
        for action in ["reservation.created", "reservation.modified", "reservation.deleted", "reservation.canceled"]:
            # Reset mocks
            self.mock_add_to_queue.calls = []
            self.mock_create_log.reset_mock()
            
            # Create test data
            test_data = {
                "_dt": datetime.now().isoformat(),
                "action": action,
                "payload": {"id": "12345"}
            }
            
            # Call the webhook endpoint
            response = self.client.post(
                "/api/stays-webhook",
                json=test_data,
                headers={"x-stays-client-id": "test", "x-stays-signature": "test"}
            )
            
            # Verify response
            self.assertEqual(response.status_code, 200, f"Failed for action: {action}")
            self.assertEqual(response.json(), {"status": "queued"}, f"Failed for action: {action}")
            
            # Verify add_to_queue was called with the right data
            self.assertEqual(len(self.mock_add_to_queue.calls), 1)
            call_args = self.mock_add_to_queue.calls[0][0][0]
            self.assertEqual(call_args, test_data)
            
            # Verify create_request_log was called
            self.mock_create_log.assert_called_once()
    
    def test_multiple_requests_are_queued(self):
        """Test that multiple webhook requests are all added to the queue"""
        # Send multiple requests
        num_requests = 5
        for i in range(num_requests):
            # Reset mocks
            self.mock_add_to_queue.calls = []
            self.mock_create_log.reset_mock()
            
            # Create test data
            test_data = {
                "_dt": datetime.now().isoformat(),
                "action": "reservation.created",
                "payload": {"id": f"{i}"}
            }
            
            # Call the webhook endpoint
            response = self.client.post(
                "/api/stays-webhook",
                json=test_data,
                headers={"x-stays-client-id": "test", "x-stays-signature": "test"}
            )
            
            # Verify response
            self.assertEqual(response.status_code, 200, f"Failed for request {i}")
            self.assertEqual(response.json(), {"status": "queued"}, f"Failed for request {i}")
            
            # Verify add_to_queue was called with the right data
            self.assertEqual(len(self.mock_add_to_queue.calls), 1)
            call_args = self.mock_add_to_queue.calls[0][0][0]
            self.assertEqual(call_args, test_data)
            
            # Verify create_request_log was called
            self.mock_create_log.assert_called_once()


if __name__ == "__main__":
    unittest.main() 