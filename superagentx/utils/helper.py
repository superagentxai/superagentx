from typing import Any
import re
import asyncio


async def sync_to_async(func, *args, **kwargs) -> Any:
    return await asyncio.to_thread(func, *args, **kwargs)


async def iter_to_aiter(iterable):
    for item in iterable:
        yield item


async def get_fstring_variables(s: str):
    # This regular expression looks for variables in curly braces
    return re.findall(r'\{(.*?)}', s)


async def ptype_to_json_scheme(ptype: str) -> str:
    match ptype:
        case 'int':
            return "integer"
        case 'str':
            return "string"
        case 'bool':
            return "boolean"
        case 'list':
            return "array"
        case 'dict' | _:
            return "object"

async def rm_trailing_spaces(data):
    """Recursively remove trailing whitespace from all string values in a JSON-like structure."""
    if isinstance(data, dict):
        return {k: await rm_trailing_spaces(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [await rm_trailing_spaces(v) for v in data]
    elif isinstance(data, str):
        return data.rstrip()  # Remove trailing whitespace
    else:
        return data
