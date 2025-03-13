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