"""Type coercion functions for schema validation."""

from pipeline.errors import ValidationError


def coerce_value(value, target_type):
    """Attempt to coerce a value to the target type."""
    if isinstance(value, target_type):
        return value

    try:
        if target_type is int:
            return _coerce_to_int(value)
        elif target_type is float:
            return _coerce_to_float(value)
        elif target_type is bool:
            return _coerce_to_bool(value)
        elif target_type is str:
            return str(value)
        else:
            raise ValidationError(
                f"Cannot coerce {type(value).__name__} "
                f"to {target_type.__name__}"
            )
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            f"Failed to coerce {value!r} "
            f"to {target_type.__name__}: {exc}"
        ) from exc


def _coerce_to_int(value):
    """Coerce a value to int."""
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError(
                "Empty string cannot be converted to int"
            )
        return int(float(value))
    return int(value)


def _coerce_to_float(value):
    """Coerce a value to float."""
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError(
                "Empty string cannot be converted to float"
            )
        return float(value)
    return float(value)


def _coerce_to_bool(value):
    """Coerce a value to bool."""
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("true", "1", "yes", "on"):
            return True
        if lower in ("false", "0", "no", "off"):
            return False
        raise ValueError(
            f"Cannot interpret {value!r} as boolean"
        )
    return bool(value)
