"""Schema validator for data records.

Validates records against a schema definition. Each field in the
schema specifies a type, whether it is required, and optionally
nested properties for object-typed fields.
"""

from pipeline.errors import ValidationError
from pipeline.schema.types import get_python_type
from pipeline.schema.coerce import coerce_value


class SchemaValidator:
    """Validates records against a schema definition."""

    def __init__(self, schema, coerce=False):
        self.schema = schema
        self.coerce = coerce

    def validate(self, record):
        """Validate a record against the schema.

        Returns the (possibly coerced) record if valid.
        Raises ValidationError if invalid.
        """
        if not isinstance(record, dict):
            raise ValidationError(
                "Record must be a dictionary"
            )

        result = dict(record)
        errors = []

        for field_name, field_spec in self.schema.items():
            required = field_spec.get("required", False)
            field_type_name = field_spec.get("type", "string")

            if field_name not in record:
                if required:
                    errors.append(
                        f"Missing required field: {field_name}"
                    )
                continue

            value = record[field_name]
            python_type = get_python_type(field_type_name)

            if not isinstance(value, python_type):
                if self.coerce:
                    try:
                        result[field_name] = coerce_value(
                            value, python_type,
                        )
                    except ValidationError as exc:
                        errors.append(
                            f"Field '{field_name}': {exc}"
                        )
                else:
                    errors.append(
                        f"Field '{field_name}': expected "
                        f"{field_type_name}, got "
                        f"{type(value).__name__}"
                    )

        if errors:
            raise ValidationError(
                f"Validation failed: {'; '.join(errors)}",
                record=record,
            )

        return result
