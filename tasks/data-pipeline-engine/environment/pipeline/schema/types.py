"""Type definitions and type registry for schema validation."""

TYPE_MAP = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "list": list,
    "dict": dict,
    "object": dict,
}


def get_python_type(type_name):
    """Return the Python type for a schema type name."""
    if type_name not in TYPE_MAP:
        raise ValueError(f"Unknown schema type: {type_name}")
    return TYPE_MAP[type_name]


def is_valid_type(type_name):
    """Check if a type name is recognized."""
    return type_name in TYPE_MAP
