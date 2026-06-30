"""Filter stage for the data pipeline."""

from pipeline.stage import Stage


class FilterStage(Stage):
    """Filter records by evaluating a predicate."""

    def __init__(self, predicate, name=None):
        super().__init__(name=name or "filter")
        if callable(predicate):
            self._filter_fn = predicate
        else:
            self._filter_fn = _compile_predicate(
                predicate,
            )

    def process(self, records, context):
        """Return only records matching the predicate."""
        filtered = []
        for record in records:
            if self._filter_fn(record):
                filtered.append(record)
                context.record_processed()
        return filtered


def _compile_predicate(predicate_str):
    """Compile a simple predicate string into a callable."""
    operators = [">=" , "<=", "!=", "==", ">", "<"]
    for op in operators:
        if op in predicate_str:
            parts = predicate_str.split(op, 1)
            if len(parts) == 2:
                field = parts[0].strip()
                raw_value = parts[1].strip()
                value = _parse_literal(raw_value)
                return _make_comparator(field, op, value)

    raise ValueError(
        f"Cannot parse predicate: {predicate_str}"
    )


def _parse_literal(raw):
    """Parse a string literal into a Python value."""
    if raw.startswith((
        "'", '"',
    )) and raw.endswith(("'", '"')):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    return raw


def _make_comparator(field, op, value):
    """Create a comparator function."""
    ops = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
    }
    compare = ops[op]

    def _filter(record):
        record_value = record.get(field)
        if record_value is None:
            return False
        return compare(record_value, value)

    return _filter
