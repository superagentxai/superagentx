import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
from typing import Any


async def sync_to_async(func, *args, **kwargs) -> Any:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(
            pool,
            functools.partial(
                func,
                *args,
                **kwargs
            ))


async def iter_to_aiter(iterable):
    for item in iterable:
        yield item
