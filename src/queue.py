import asyncio

from .actions import SummaryAction

# TODO: migrate to RQ

_queue = asyncio.Queue()

async def enqueue(action: SummaryAction):
    """Add an item to the queue."""
    await _queue.put(action)


async def dequeue():
    """Remove and return the next item from the queue."""
    action = await _queue.get()
    _queue.task_done()
    return action

def queue_size():
    return _queue.qsize()

def is_empty():
    return _queue.empty()