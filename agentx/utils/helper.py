from typing import Any

import asyncio


async def sync_to_async(func, *args, **kwargs) -> Any:
    await asyncio.to_thread(func, *args, **kwargs)


async def iter_to_aiter(iterable):
    for item in iterable:
        yield item
