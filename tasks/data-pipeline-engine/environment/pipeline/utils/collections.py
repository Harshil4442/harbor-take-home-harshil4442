"""Collection utility functions for pipeline processing."""


def group_by(records, key):
    """Group a list of records by a key field."""
    groups = {}
    for record in records:
        group_key = record.get(key)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(record)
    return groups


def flatten(nested_list):
    """Flatten a list of lists into a single list."""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def chunk(lst, size):
    """Split a list into chunks of the given size."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def pick(record, fields):
    """Select only the specified fields from a record."""
    return {k: v for k, v in record.items() if k in fields}


def omit(record, fields):
    """Remove the specified fields from a record."""
    return {k: v for k, v in record.items() if k not in fields}
