import asyncio
from typing import Any


async def sync_to_async(func, *args, **kwargs) -> Any:
    await asyncio.to_thread(func, *args, **kwargs)


async def iter_to_aiter(iterable):
    for item in iterable:
        yield item
