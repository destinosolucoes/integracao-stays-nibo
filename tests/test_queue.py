#!/usr/bin/env python
"""
Tests for the queue operations to ensure items are added and processed in order
"""
import sys
import os
import asyncio
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

# Add the parent directory to sys.path to allow for importing the API modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Mock module to avoid DB connection issues
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlmodel'] = MagicMock()

# Import queue functions
from api.queue import (
    add_to_queue,
    queue_size,
    start_queue_processor,
    stop_queue_processor,
    webhook_queue
)


class TestQueue(unittest.IsolatedAsyncioTestCase):
    """Tests for the queue operations"""
    
    async def asyncSetUp(self):
        """Set up before each test"""
        # Clear the queue before each test
        while not webhook_queue.empty():
            try:
                webhook_queue.get_nowait()
                webhook_queue.task_done()
            except asyncio.QueueEmpty:
                break
    
    async def test_add_to_queue(self):
        """Test adding items to the queue"""
        # Add an item to the queue
        item = {
            "_dt": datetime.now().isoformat(),
            "action": "reservation.created",
            "payload": {"id": "12345"}
        }
        await add_to_queue(item)
        
        # Check queue size
        self.assertEqual(queue_size(), 1)
        
        # Get the item from the queue and verify it's the same
        queue_item = await webhook_queue.get()
        webhook_queue.task_done()
        
        self.assertEqual(queue_item, item)
    
    async def test_queue_order(self):
        """Test that items are processed in the order they are added (FIFO)"""
        # Create test items
        items = [
            {
                "_dt": datetime.now().isoformat(),
                "action": f"reservation.created.{i}",
                "payload": {"id": f"{i}"}
            }
            for i in range(5)
        ]
        
        # Add items to the queue
        for item in items:
            await add_to_queue(item)
        
        # Check queue size
        self.assertEqual(queue_size(), 5)
        
        # Get items from the queue and verify order
        retrieved_items = []
        for _ in range(5):
            item = await webhook_queue.get()
            retrieved_items.append(item)
            webhook_queue.task_done()
        
        # Check that items are retrieved in the same order they were added
        for i in range(5):
            self.assertEqual(retrieved_items[i], items[i])
    
    @patch('api.queue._processor_task')
    @patch('api.queue.asyncio.create_task')
    async def test_start_stop_processor(self, mock_create_task, mock_processor_task):
        """Test starting and stopping the queue processor"""
        # Create mock processor function
        mock_processor = AsyncMock()
        
        # Set up our mocks to simulate processor already running
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_create_task.return_value = mock_task
        
        # Configure the mock processor task
        mock_processor_task.done.return_value = False
        
        # Test that start_queue_processor doesn't create a new task if one is already running
        with patch('api.queue._processor_running', True):
            start_queue_processor(mock_processor)
            mock_create_task.assert_not_called()
        
        # Test that start_queue_processor creates a task if none is running
        with patch('api.queue._processor_running', False):
            mock_processor_task.done.return_value = True
            start_queue_processor(mock_processor)
            mock_create_task.assert_called_once()
        
        # Test stop_queue_processor
        mock_processor_task.done.return_value = False
        
        # When we call stop_queue_processor, it should call cancel on the processor task
        with patch('api.queue._processor_running', True):
            stop_queue_processor()
            mock_processor_task.cancel.assert_called_once()
    
    async def test_process_queue_processes_items(self):
        """Test that the queue processor processes items in order"""
        # Create test items
        items = [
            {
                "_dt": datetime.now().isoformat(),
                "action": f"reservation.created.{i}",
                "payload": {"id": f"{i}"}
            }
            for i in range(3)
        ]
        
        # Add items to the queue
        for item in items:
            await add_to_queue(item)
        
        # Create a mock processor function that records the items it processes
        processed_items = []
        
        async def mock_processor(item):
            processed_items.append(item)
            return {"status": "processed"}
        
        # Start the processor
        processor_task = asyncio.create_task(
            _run_processor_for_test(mock_processor)
        )
        
        # Wait for all items to be processed
        await webhook_queue.join()
        
        # Cancel the processor task
        processor_task.cancel()
        try:
            await processor_task
        except asyncio.CancelledError:
            pass
        
        # Check that all items were processed in the right order
        self.assertEqual(len(processed_items), 3)
        for i in range(3):
            self.assertEqual(processed_items[i], items[i])


async def _run_processor_for_test(processor_func):
    """Run the processor for test purposes"""
    while True:
        # Get item from queue
        item = await webhook_queue.get()
        
        try:
            # Process the item
            await processor_func(item)
        finally:
            # Mark task as done
            webhook_queue.task_done()


if __name__ == "__main__":
    unittest.main() 