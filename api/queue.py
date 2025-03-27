import asyncio
import logging
from typing import Dict, Any, Callable, Coroutine, Optional

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Main queue for processing webhook requests
webhook_queue = asyncio.Queue()

# Flag to track if processor is running
_processor_running = False

async def process_queue(processor_func: Callable[[Dict[str, Any]], Coroutine]):
    """
    Process items from the queue continuously
    
    Args:
        processor_func: The coroutine function that processes each queue item
    """
    global _processor_running
    
    if _processor_running:
        return
        
    _processor_running = True
    
    try:
        logger.info("Queue processor started")
        while True:
            try:
                # Get item from queue with timeout to allow for graceful shutdown
                item = await asyncio.wait_for(webhook_queue.get(), timeout=1.0)
                
                try:
                    # Process the item
                    await processor_func(item)
                    logger.info(f"Processed webhook request: {item.get('action', 'unknown')}")
                except Exception as e:
                    logger.error(f"Error processing webhook request: {str(e)}")
                finally:
                    # Mark task as done
                    webhook_queue.task_done()
                    
            except asyncio.TimeoutError:
                # Just a timeout, continue waiting
                pass
            except asyncio.CancelledError:
                # Cancel was called, exit gracefully
                break
            except Exception as e:
                logger.error(f"Unexpected error in queue processor: {str(e)}")
                # Wait a bit before retrying to avoid cpu spinning on persistent errors
                await asyncio.sleep(1)
    finally:
        _processor_running = False
        logger.info("Queue processor stopped")

async def add_to_queue(item: Dict[str, Any]) -> None:
    """
    Add an item to the webhook processing queue
    
    Args:
        item: The webhook data to process
    """
    await webhook_queue.put(item)
    logger.info(f"Added webhook request to queue: {item.get('action', 'unknown')}")

def queue_size() -> int:
    """Get the current size of the queue"""
    return webhook_queue.qsize()

# Task reference to manage the queue processor
_processor_task: Optional[asyncio.Task] = None

def start_queue_processor(processor_func: Callable[[Dict[str, Any]], Coroutine]) -> None:
    """
    Start the queue processor in the background
    
    Args:
        processor_func: The coroutine function that processes each queue item
    """
    global _processor_task
    
    if _processor_task and not _processor_task.done():
        logger.info("Queue processor is already running")
        return
    
    _processor_task = asyncio.create_task(process_queue(processor_func))
    logger.info("Queue processor task created")

def stop_queue_processor() -> None:
    """Stop the queue processor task"""
    global _processor_task
    
    if _processor_task and not _processor_task.done():
        _processor_task.cancel()
        logger.info("Queue processor task cancelled") 