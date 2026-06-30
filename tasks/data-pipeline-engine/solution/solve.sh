#!/usr/bin/env bash
set -euo pipefail

# ── Fix Bug 1: Nested schema validation ──────────────────
# The validator must recursively validate nested object properties.
cat > /app/src/pipeline/schema/validator.py << 'VALIDATOR_EOF'
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
        return self._validate_against_schema(
            record, self.schema,
        )

    def _validate_against_schema(self, record, schema):
        """Validate a record against a schema dict."""
        result = dict(record)
        errors = []

        for field_name, field_spec in schema.items():
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
            elif (
                field_type_name == "object"
                and "properties" in field_spec
            ):
                try:
                    result[field_name] = (
                        self._validate_against_schema(
                            value, field_spec["properties"],
                        )
                    )
                except ValidationError as nested_exc:
                    errors.append(
                        f"Field '{field_name}': {nested_exc}"
                    )

        if errors:
            raise ValidationError(
                f"Validation failed: {'; '.join(errors)}",
                record=record,
            )

        return result
VALIDATOR_EOF

# ── Fix Bug 2: Quarantine error recovery ─────────────────
# The quarantine handler must return True, not re-raise.
cat > /app/src/pipeline/recovery/handler.py << 'HANDLER_EOF'
"""Error recovery handlers for pipeline stages."""

from pipeline.errors import PipelineError


class ErrorHandler:
    """Dispatches error handling to the appropriate strategy."""

    def __init__(self, strategy="fail-fast"):
        if strategy not in ("fail-fast", "skip", "quarantine"):
            raise ValueError(
                f"Unknown error strategy: {strategy}"
            )
        self.strategy = strategy
        self._handlers = {
            "fail-fast": FailFastHandler(),
            "skip": SkipHandler(),
            "quarantine": QuarantineHandler(),
        }

    def handle(self, error, record, context):
        """Handle an error using the configured strategy."""
        handler = self._handlers[self.strategy]
        return handler.handle(error, record, context)


class FailFastHandler:
    """Stop the pipeline immediately on error."""

    def handle(self, error, record, context):
        """Re-raise the error to halt the pipeline."""
        context.metrics["failed"] += 1
        raise error


class SkipHandler:
    """Skip the failed record and continue processing."""

    def handle(self, error, record, context):
        """Log the error and signal to continue."""
        context.metrics["failed"] += 1
        context.metrics["skipped"] += 1
        return True


class QuarantineHandler:
    """Move failed records to quarantine and continue."""

    def handle(self, error, record, context):
        """Add to quarantine and continue processing."""
        context.metrics["failed"] += 1
        context.metrics["quarantined"] += 1
        context.quarantine.append({
            "record": record,
            "error": str(error),
            "stage": getattr(error, "stage", None),
        })
        return True
HANDLER_EOF

# ── Fix Bug 3: Per-group AVG in aggregation ──────────────
# Use len(values) instead of total_count for AVG.
cat > /app/src/pipeline/stages/aggregate.py << 'AGGREGATE_EOF'
"""Aggregation stage for the data pipeline."""

from pipeline.stage import Stage
from pipeline.utils.collections import group_by


class AggregateStage(Stage):
    """Aggregate records by grouping and computing summaries."""

    def __init__(self, group_field, aggregations, name=None):
        super().__init__(name=name or "aggregate")
        self.group_field = group_field
        self.aggregations = aggregations

    def process(self, records, context):
        """Group records and compute aggregations."""
        if not records:
            return []

        groups = group_by(records, self.group_field)
        results = []

        for group_key, group_records in groups.items():
            result = {self.group_field: group_key}

            for agg in self.aggregations:
                field = agg["field"]
                operation = agg["operation"].lower()
                alias = agg.get(
                    "alias", f"{operation}_{field}",
                )

                values = [
                    r[field]
                    for r in group_records
                    if field in r and r[field] is not None
                ]

                if operation == "sum":
                    result[alias] = (
                        sum(values) if values else 0
                    )
                elif operation == "avg":
                    result[alias] = (
                        sum(values) / len(values)
                        if values
                        else 0
                    )
                elif operation == "count":
                    result[alias] = len(values)
                elif operation == "min":
                    result[alias] = (
                        min(values) if values else None
                    )
                elif operation == "max":
                    result[alias] = (
                        max(values) if values else None
                    )
                else:
                    raise ValueError(
                        f"Unknown aggregation: "
                        f"{operation}"
                    )

            results.append(result)
            context.record_processed()

        return results
AGGREGATE_EOF

# ── Fix Bug 4: Computed field dependency resolution ──────
# Evaluate expressions against result (updated) not snapshot.
cat > /app/src/pipeline/stages/transform.py << 'TRANSFORM_EOF'
"""Transformation stage for the data pipeline."""

from pipeline.stage import Stage
from pipeline.utils.expressions import evaluate_expression
from pipeline.errors import TransformError
from pipeline.recovery.handler import ErrorHandler


class TransformStage(Stage):
    """Transform records by applying field operations."""

    def __init__(
        self, transforms, error_strategy="fail-fast",
        name=None,
    ):
        super().__init__(name=name or "transform")
        self.transforms = transforms
        self.error_handler = ErrorHandler(
            strategy=error_strategy,
        )

    def process(self, records, context):
        """Apply transforms to each record."""
        results = []
        for record in records:
            try:
                transformed = self._apply_transforms(
                    record,
                )
                results.append(transformed)
                context.record_processed()
            except TransformError as exc:
                exc.stage = self.name
                try:
                    self.error_handler.handle(
                        exc, record, context,
                    )
                except TransformError:
                    raise
        return results

    def _apply_transforms(self, record):
        """Apply all transforms to a single record."""
        result = dict(record)

        for transform in self.transforms:
            t_type = transform.get("type", "compute")

            if t_type == "rename":
                old_name = transform["from"]
                new_name = transform["to"]
                if old_name in result:
                    result[new_name] = result.pop(old_name)

            elif t_type == "set":
                result[transform["field"]] = (
                    transform["value"]
                )

            elif t_type == "compute":
                field = transform["field"]
                expr = transform["expr"]
                try:
                    value = evaluate_expression(
                        expr, result,
                    )
                    result[field] = value
                except (
                    ValueError,
                    ZeroDivisionError,
                ) as exc:
                    raise TransformError(
                        f"Failed to compute field "
                        f"'{field}': {exc}",
                        field=field,
                        expression=expr,
                        record=record,
                    ) from exc

            else:
                raise TransformError(
                    f"Unknown transform type: {t_type}",
                    record=record,
                )

        return result
TRANSFORM_EOF
