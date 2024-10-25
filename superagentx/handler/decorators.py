import functools


def tool(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    wrapper._is_handler_tool = True
    return wrapper