"""Bound external work without releasing capacity while a cancelled thread runs."""
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException

_slots = threading.BoundedSemaphore(8)
_workers = ThreadPoolExecutor(max_workers=8, thread_name_prefix="external-work")


async def run_blocking(function, *args, **kwargs):
    if not _slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="The service is busy. Please try again shortly.")
    try:
        future = _workers.submit(function, *args, **kwargs)
    except BaseException:
        _slots.release()
        raise
    # A cancelled await does not release admission until the actual work ends.
    # The callback also handles cancellation before a worker starts.
    future.add_done_callback(lambda _: _slots.release())
    return await asyncio.wrap_future(future)


_agent_slots = threading.BoundedSemaphore(8)

async def run_agent(function, *args):
    if not _agent_slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="The career agent is busy. Please try again shortly.")
    try:
        return await asyncio.wait_for(function(*args), timeout=300)
    finally:
        _agent_slots.release()
