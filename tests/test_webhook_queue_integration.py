#!/usr/bin/env python
"""
Integration tests for the end-to-end flow from webhook to queue to processor
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

# Create mock module for webhook_processor
mock_webhook_processor = MagicMock()
mock_webhook_processor.process_webhook_request = AsyncMock()
sys.modules['api.webhook_processor'] = mock_webhook_processor


class TestWebhookQueueIntegration(unittest.IsolatedAsyncioTestCase):
    """Tests for the end-to-end webhook to queue to processor flow"""
    
    async def asyncSetUp(self):
        """Set up before each test"""
        # Import real queue module
        if 'api.queue' in sys.modules:
            del sys.modules['api.queue']
        
        # Create mocks
        self.mock_validate_header = patch('api.utils.validate_header').start()
        self.mock_validate_header.return_value = True
        
        self.mock_create_log = patch('api.utils.create_request_log').start()
        
        self.mock_processor = AsyncMock()
        self.mock_processor.return_value = {"status": "processed"}
        
        # Make sure we use the real queue implementation
        import api.queue
        
        # Clear the queue
        while not api.queue.webhook_queue.empty():
            try:
                api.queue.webhook_queue.get_nowait()
                api.queue.webhook_queue.task_done()
            except asyncio.QueueEmpty:
                break
    
    async def asyncTearDown(self):
        """Clean up after each test"""
        patch.stopall()
        
        # Import real queue module
        if 'api.queue' in sys.modules:
            # Stop the queue processor if running
            import api.queue
            api.queue.stop_queue_processor()
    
    async def test_webhook_to_queue_to_processor(self):
        """Test that requests flow from webhook to queue to processor"""
        # Import FastAPI app and queue
        from api.index import app
        import api.queue
        
        # Create a list to hold processed items
        processed_items = []
        
        # Create processor function that records items
        async def test_processor(item):
            processed_items.append(item)
            return {"status": "processed"}
        
        # Start the queue processor with our test processor
        api.queue.start_queue_processor(test_processor)
        
        # Create FastAPI test client
        client = TestClient(app)
        
        # Create test data
        test_items = [
            {
                "_dt": datetime.now().isoformat(),
                "action": f"reservation.test.{i}",
                "payload": {"id": f"{i}"}
            }
            for i in range(3)
        ]
        
        # Send requests to webhook endpoint
        for item in test_items:
            response = client.post(
                "/api/stays-webhook",
                json=item,
                headers={"x-stays-client-id": "test", "x-stays-signature": "test"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "queued"})
        
        # Wait for queue to process all items
        # This is tricky in an integration test, so we'll use a simple approach
        # Wait until we've processed all items or hit a timeout
        for _ in range(30):  # Try for 3 seconds max
            if len(processed_items) == len(test_items):
                break
            await asyncio.sleep(0.1)
        
        # Verify all items were processed
        self.assertEqual(len(processed_items), len(test_items))
        
        # Verify items were processed in the correct order
        for i, item in enumerate(test_items):
            self.assertEqual(processed_items[i], item)
    
    async def test_concurrent_webhook_requests(self):
        """Test handling concurrent webhook requests"""
        # Import FastAPI app and queue
        from api.index import app
        import api.queue
        
        # Create a list to hold processed items
        processed_items = []
        
        # Create processor function that records items
        async def test_processor(item):
            # Add a small delay to simulate processing time
            await asyncio.sleep(0.05)
            processed_items.append(item)
            return {"status": "processed"}
        
        # Start the queue processor with our test processor
        api.queue.start_queue_processor(test_processor)
        
        # Create FastAPI test client
        client = TestClient(app)
        
        # Create test data
        num_requests = 10
        test_items = [
            {
                "_dt": datetime.now().isoformat(),
                "action": f"reservation.concurrent.{i}",
                "payload": {"id": f"{i}"}
            }
            for i in range(num_requests)
        ]
        
        # Prepare asynchronous requests
        async def send_request(item):
            # Use the synchronous client in a thread to simulate concurrent requests
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.post(
                    "/api/stays-webhook",
                    json=item,
                    headers={"x-stays-client-id": "test", "x-stays-signature": "test"}
                )
            )
            return response
        
        # Send requests concurrently
        tasks = [send_request(item) for item in test_items]
        responses = await asyncio.gather(*tasks)
        
        # Verify all responses
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "queued"})
        
        # Wait for queue to process all items
        for _ in range(50):  # Try for 5 seconds max
            if len(processed_items) == num_requests:
                break
            await asyncio.sleep(0.1)
        
        # Verify all items were processed
        self.assertEqual(len(processed_items), num_requests)
        
        # Verify all items were processed (order doesn't matter in this test)
        for item in test_items:
            self.assertIn(item, processed_items)


class TestQueueProcessorLifecycle(unittest.IsolatedAsyncioTestCase):
    """Tests for the queue processor lifecycle"""
    
    async def asyncSetUp(self):
        """Set up before each test"""
        # Import real queue module
        if 'api.queue' in sys.modules:
            del sys.modules['api.queue']
        
        # Make sure we use the real queue implementation
        import api.queue
        
        # Clear the queue
        while not api.queue.webhook_queue.empty():
            try:
                api.queue.webhook_queue.get_nowait()
                api.queue.webhook_queue.task_done()
            except asyncio.QueueEmpty:
                break
    
    async def asyncTearDown(self):
        """Clean up after each test"""
        # Import real queue module
        if 'api.queue' in sys.modules:
            # Stop the queue processor if running
            import api.queue
            api.queue.stop_queue_processor()
    
    async def test_processor_handles_errors_and_continues(self):
        """Test that the processor handles errors and continues processing"""
        # Import queue
        import api.queue
        
        # Create processor function that sometimes fails
        call_count = 0
        processed_items = []
        error_on_items = [1, 3]  # Fail on these item indices
        
        async def failing_processor(item):
            nonlocal call_count
            if call_count in error_on_items:
                call_count += 1
                raise Exception(f"Test error on item {item}")
            call_count += 1
            processed_items.append(item)
            return {"status": "processed"}
        
        # Start the queue processor with our failing processor
        api.queue.start_queue_processor(failing_processor)
        
        # Add test items to the queue
        test_items = [
            {
                "_dt": datetime.now().isoformat(),
                "action": f"reservation.test.{i}",
                "payload": {"id": f"{i}"}
            }
            for i in range(5)
        ]
        
        for item in test_items:
            await api.queue.add_to_queue(item)
        
        # Wait for all items to be processed
        for _ in range(50):  # Try for 5 seconds max
            if call_count >= len(test_items):  # All items were attempted
                break
            await asyncio.sleep(0.1)
        
        # Verify all items were attempted
        self.assertEqual(call_count, len(test_items))
        
        # Verify non-error items were processed
        self.assertEqual(len(processed_items), len(test_items) - len(error_on_items))
        
        # Verify the right items were processed
        expected_processed = [test_items[i] for i in range(len(test_items)) if i not in error_on_items]
        for item in expected_processed:
            self.assertIn(item, processed_items)


if __name__ == "__main__":
    unittest.main() 