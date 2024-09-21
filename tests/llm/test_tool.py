import inspect
from typing import get_type_hints


def get_delivery_date(order_id: str, id: int) -> str:
    """Get the delivery date for a customer's order. Call this whenever you need to know
       the delivery date, for example when a customer asks 'Where is my package"""
    return "test"


def generate_function_json(func) -> dict:
    # Get function name
    func_name = func.__name__

    # Get function docstring
    docstring = inspect.getdoc(func)

    # Get function annotations (parameter types and return llm_type)
    type_hints = get_type_hints(func)

    # Generate the 'properties' field based on function parameters
    properties = {}
    for param, param_type in type_hints.items():
        if param != 'return':
            properties[param] = {
                "llm_type": param_type.__name__,
                "description": f"The {param.replace('_', ' ')}."
            }

    # Create the final JSON structure
    function_json = {
        "function": {
            "name": func_name,
            "description": docstring,
            "parameters": {
                "llm_type": "object",
                "properties": properties,
                "required": list(properties.keys()),
                "additionalProperties": False
            }
        }
    }
    # return json.dumps(function_json, indent=4)
    return function_json


# Generate JSON for the function
function_json = generate_function_json(get_delivery_date)
tool = [function_json]
